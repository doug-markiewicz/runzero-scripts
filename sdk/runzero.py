# This script leverages runZero's python SDK to pull assets from a SaaS instance 
# into a self hosted instance. This allows use of the SaaS console for perimeter
# scanning, leveraging runZero's hosted explorers.

from dotenv import load_dotenv
import requests
import os
import uuid
import json
from datetime import datetime
from flatten_json import flatten
from ipaddress import ip_address
from typing import Any, Dict, List
import runzero
from runzero.client import AuthError
from runzero.api import CustomAssets, Sites
from runzero.types import (CustomAttribute,ImportAsset,IPv4Address,IPv6Address,NetworkInterface,ImportTask)

load_dotenv()

# Configure SaaS runZero environment
RUNZERO_SAAS_ADDR = 'console.runzero.com'
RUNZERO_SAAS_ORG_ID = '98828456-f9ee-485d-aff6-11ddc91b2468'
RUNZERO_SAAS_SITE_NAME = 'Perimeter'
RUNZERO_SAAS_SITE_ID = 'd3cb8226-f531-41a6-a334-a0bb7e981460'
RUNZERO_SAAS_CLIENT_ID = os.getenv("RUNZERO_CLIENT_ID")
RUNZERO_SAAS_CLIENT_SECRET = os.getenv("RUNZERO_CLIENT_SECRET")

# Configure self hosted runZero environment
RUNZERO_HOSTED_ADDR = '192.168.2.200'
RUNZERO_HOSTED_ORG_ID = '3a1edcc5-12f9-4ff2-a2e8-99364157e5ac'
RUNZERO_HOSTED_SITE_NAME = 'Perimeter'
RUNZERO_HOSTED_SITE_ID = '00e12372-c88a-4154-9532-6333d420460c'
RUNZERO_HOSTED_CUSTOM_INT_ID = '250f7449-9046-491b-b079-533a8673cb43'
RUNZERO_HOSTED_IMPORT_TASK_NAME = 'runZero SaaS Sync - Perimeter'
RUNZERO_HOSTED_CLIENT_ID = os.getenv("RUNZERO_HOSTED_CLIENT_ID")
RUNZERO_HOSTED_CLIENT_SECRET = os.getenv("RUNZERO_HOSTED_CLIENT_SECRET")

# Authentication with client ID and secret and obtain bearer token
def get_token(address, client_id, client_secret):
    token_request_url = f'https://{address}/api/v1.0/account/api/token'
    token_request_header = {"Content-Type": "application/x-www-form-urlencoded"}
    token_request_data = {"grant_type": "client_credentials"}
    token_response = requests.post(token_request_url, data=token_request_data, headers=token_request_header, verify=False, auth=(client_id, client_secret))
    if token_response.status_code != 200:
        print('failed to obtain token from oauth server')
        print('request_url:', token_request_url)
        print(client_id, client_secret)
        print('token_response.status_code:', token_response.status_code)
        exit(1)
    else:
        token_json = json.loads(token_response.text)
        return token_json['access_token']    

### NEEDS UPDATED ###
def build_assets_from_json(json_input: List[Dict[str, Any]]) -> List[ImportAsset]:
    assets: List[ImportAsset] = []
    for i in json_input:
        item = i["node"]
        tanium_oid = item.get('id', uuid.uuid4)
        tanium_hostname = item.get('name', '')
        tanium_macs = item.get('macAddresses', [])
        tanium_address = item.get('ipAddress', '')
        tanium_domain = item.get('domainName', '')
        tanium_first_seen = item.get('eidFirstSeen', '')
        tanium_os_name = item.get('os', {}).get('name', '')
        tanium_manufacturer = item.get('manufacturer', '')
        tanium_model = item.get('model', '')

        # create network interfaces
        networks = []
        if len(tanium_macs) > 0 and isinstance(tanium_macs, list):
            for mac in tanium_macs:
                if len(mac) <= 23:
                    network = build_network_interface(ips=[tanium_address], mac=mac)
                    networks.append(network)
                else:
                    network = build_network_interface(ips=[tanium_address], mac=None)
                    networks.append(network)
        else:
            network = build_network_interface(ips=[tanium_address], mac=None)
            networks.append(network)
        
        # handle any additional values and insert into custom_attrs
        custom_attrs: Dict[str, CustomAttribute] = {}

        root_keys_to_ignore = []
        for key, value in item.items():
            if not isinstance(value, dict):
                root_keys_to_ignore.append(key)

        flattened_items = flatten(nested_dict=item,
                                  root_keys_to_ignore=root_keys_to_ignore)

        item = flattened_items | item

        for key, value in item.items():
            if not isinstance(value, dict):
                custom_attrs[key] = CustomAttribute(str(value)[:1023])

        # Build assets for import 
        assets.append(
            ImportAsset(
                id=tanium_oid,
                networkInterfaces=networks,
                hostnames=[tanium_hostname],
                domain=tanium_domain,
                os=tanium_os_name,
                firstSeenTS=tanium_first_seen,
                manufacturer=tanium_manufacturer,
                model=tanium_model,
                customAttributes=custom_attrs
            )
        )
    return assets

### UPDATED ###
def build_network_interface(ips: List[str], mac: str = None) -> NetworkInterface:
     
    # This function converts a mac and a list of strings in either ipv4 or ipv6 format 
    # and creates a NetworkInterface that is accepted in the ImportAsset
    
    ip4s: List[IPv4Address] = []
    ip6s: List[IPv6Address] = []
    for ip in ips[:99]:
        try:
            ip_addr = ip_address(ip)
            if ip_addr.version == 4:
                ip4s.append(ip_addr)
            elif ip_addr.version == 6:
                ip6s.append(ip_addr)
            else:
                continue
        except:
            continue
    if mac is None or not isinstance(mac, str) or mac == "[no results]":
        return NetworkInterface(ipv4Addresses=ip4s, ipv6Addresses=ip6s)
    else:     
        return NetworkInterface(macAddress=mac, ipv4Addresses=ip4s, ipv6Addresses=ip6s)

### UPDATED ###
def import_data_to_runzero(assets: List[ImportAsset]):

    # create the runzero client
    c = runzero.Client()

    # try to log in using OAuth credentials
    try:
        c.oauth_login(RUNZERO_HOSTED_CLIENT_ID, RUNZERO_HOSTED_CLIENT_SECRET)
    except AuthError as e:
        print(f'login failed: {e}')
        return

    # create the site manager to get our site information; set site ID for any new hosts
    site_mgr = Sites(c)
    site = site_mgr.get(RUNZERO_HOSTED_ORG_ID, RUNZERO_HOSTED_SITE_NAME)
    if not site:
        print(f'unable to find requested site')
        return

    # create the import manager to upload custom assets
    import_mgr = CustomAssets(c)
    import_task = import_mgr.upload_assets(org_id=RUNZERO_HOSTED_ORG_ID, site_id=RUNZERO_HOSTED_SITE_ID, custom_integration_id=RUNZERO_HOSTED_CUSTOM_INT_ID, assets=assets, task_info=ImportTask(name=RUNZERO_HOSTED_IMPORT_TASK_NAME))

    if import_task:
        print(f'task created! view status here: https://{RUNZERO_HOSTED_ADDR}/tasks?task={import_task.id}')
        
def main():

    # Authenticate to SaaS and self-hosted consoles
    saas_token = get_token(RUNZERO_SAAS_ADDR, RUNZERO_SAAS_CLIENT_ID, RUNZERO_SAAS_CLIENT_SECRET)
    hosted_token = get_token(RUNZERO_HOSTED_ADDR, RUNZERO_HOSTED_CLIENT_ID, RUNZERO_HOSTED_CLIENT_SECRET)
    
    # Set search query for assets to be pulled from SaaS instance
    asset_filter = 'site:=Perimeter'

    # Export assets from SaaS instance
    request_url = f'https://{RUNZERO_SAAS_ADDR}/api/v1.0/export/org/assets.json?search={asset_filter}&_oid={RUNZERO_SAAS_ORG_ID}'
    assets = requests.get(request_url, headers={"Content-Type": "application/json", "Authorization": "Bearer " + saas_token})
    
    # Parse JSON object; NOT SURE IF THIS IS NEEDED
    assets_json = assets.json()
    print(assets_json)

    # Format asset list for import into runZero
    print(str(datetime.now()) + f" Building assets for import into runZero.")                
    import_assets = build_assets_from_json(assets_json)

    # Import assets into runZero
    print(str(datetime.now()) + f" Importing assets into runZero.")
    #import_data_to_runzero(assets=import_assets)

if __name__ == '__main__':
    main()