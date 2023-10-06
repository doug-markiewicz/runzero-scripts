# runZero Python SDK script for Lima Charlie
# Last updated 10/6/2023

# Docs: https://www.runzero.com/docs/integrations-inbound/
# Docs: https://pypi.org/project/runzero-sdk/ 
# Docs: https://doc.limacharlie.io/docs/documentation/dec140b42ad78-api-keys
# Docs: https://doc.limacharlie.io/docs/api/43897cbb915ef-lima-charlie-io-rest-api

import requests
import os
import uuid
import json
from flatten_json import flatten
from ipaddress import ip_address
from typing import Any, Dict, List
import runzero
from runzero.client import AuthError
from runzero.api import CustomAssets, Sites
from runzero.types import (CustomAttribute,ImportAsset,IPv4Address,IPv6Address,NetworkInterface,ImportTask)

'''   
    The following attributes need to be configured to match the account that is being queried. If you are a SaaS customer, the base url and token url
    should remain the same. If you have an on-premise deployment, then console.runzero.com will need to be updated with the console address. This 
    script uses the account API credentials for authentication. Visiting the following URL for instructions on creating account API credentials.

    https://www.runzero.com/docs/leveraging-the-api/#account-api

    If you'd like to seperate out credentials, they can be imported from a seperate file.

    Example:

    import lc_config
    RUNZERO_CLIENT_ID = lc_config.RUNZERO_CLIENT_ID
    RUNZERO_CLIENT_SECRET = lc_config.RUNZERO_CLIENT_SECRET
    LIMACHARLIE_API_KEY = lc_config.LIMACHARLIE_API_KEY
'''

# Configure runZero environment
RUNZERO_BASE_URL = 'https://console.runZero.com/api/v1.0'
RUNZERO_ORG_ID = ' '
RUNZERO_CUSTOM_SOURCE_ID = ' ' 
RUNZERO_SITE_NAME = 'LimaCharlie Unknown Assets'
RUNZERO_SITE_ID = ' '
RUNZERO_IMPORT_TASK_NAME = 'LimaCharlie Sync'
RUNZERO_CLIENT_ID = ' '
RUNZERO_CLIENT_SECRET = ' '

# Configure LimaCharlie environment
LIMACHARLIE_JWT_URL = 'https://jwt.limacharlie.io/'
LIMACHARLIE_BASE_URL = 'https://api.limacharlie.io/v1'
LIMACHARLIE_OID = ' '
LIMACHARLIE_API_KEY = ' '

def build_assets_from_json(json_input: List[Dict[str, Any]]) -> List[ImportAsset]:
    assets: List[ImportAsset] = []
    for item in json_input:
        # grab known API attributes from the json dict that are always present
        sensor_oid = item.get('oid', uuid.uuid4)
        sensor_hostname = item.get('hostname', '')
        sensor_macs = item.get('mac_addr', [])
        sensor_address = item.get('int_ip', '')

        # create network interfaces
        networks = []
        if len(sensor_macs) > 0 and isinstance(sensor_macs, list):
            for mac in sensor_macs:
                if len(mac) <= 23:
                    network = build_network_interface(ips=[sensor_address], mac=mac)
                    networks.append(network)
                else:
                    network = build_network_interface(ips=[sensor_address], mac=None)
                    networks.append(network)
        else:
            network = build_network_interface(ips=[sensor_address], mac=None)
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
                id=sensor_oid,
                network_interfaces=[network],
                hostnames=[sensor_hostname],
                customAttributes=custom_attrs
            )
        )
    return assets

# *** Should not need to touch this ***
def build_network_interface(ips: List[str], mac: str = None) -> NetworkInterface:
    ''' 
    This function converts a mac and a list of strings in either ipv4 or ipv6 format and creates a NetworkInterface that
    is accepted in the ImportAsset
    '''
    ip4s: List[IPv4Address] = []
    ip6s: List[IPv6Address] = []
    for ip in ips[:99]:
        ip_addr = ip_address(ip)
        if ip_addr.version == 4:
            ip4s.append(ip_addr)
        elif ip_addr.version == 6:
            ip6s.append(ip_addr)
        else:
            continue
    if mac is None:
        return NetworkInterface(ipv4Addresses=ip4s, ipv6Addresses=ip6s)
    else:
        return NetworkInterface(macAddress=mac, ipv4Addresses=ip4s, ipv6Addresses=ip6s)


def import_data_to_runzero(assets: List[ImportAsset]):
    '''
    The code below gives an example of how to create a custom source and upload valid assets from a CSV to a site using
    the new custom source.
    '''
    # create the runzero client
    c = runzero.Client()

    # try to log in using OAuth credentials
    try:
        c.oauth_login(RUNZERO_CLIENT_ID, RUNZERO_CLIENT_SECRET)
    except AuthError as e:
        print(f'login failed: {e}')
        return

    # create the site manager to get our site information; set site ID for any new hosts
    site_mgr = Sites(c)
    site = site_mgr.get(RUNZERO_ORG_ID, RUNZERO_SITE_NAME)
    if not site:
        print(f'unable to find requested site')
        return

    # create the import manager to upload custom assets
    import_mgr = CustomAssets(c)
    import_task = import_mgr.upload_assets(org_id=RUNZERO_ORG_ID, site_id=RUNZERO_SITE_ID, custom_integration_id=RUNZERO_CUSTOM_SOURCE_ID, assets=assets, task_info=ImportTask(name=RUNZERO_IMPORT_TASK_NAME))

    if import_task:
        print(f'task created! view status here: https://console.runzero.com/tasks?task={import_task.id}')

def main():

    # Request and parse JSON web token
    jwt_url = f'{LIMACHARLIE_JWT_URL}?oid={LIMACHARLIE_OID}&secret={LIMACHARLIE_API_KEY}'
    jwt = requests.post(jwt_url, '')
    token = jwt.json()

    # Request Lima Charlie sensor list
    lima_charlie_token = token['jwt']
    api_header = {'Authorization': f'Bearer {lima_charlie_token}'}
    api_url = f'{LIMACHARLIE_BASE_URL}/sensors/{LIMACHARLIE_OID}'
    sensors = requests.get(api_url, headers=api_header)
    
    # Parse JSON object to native python object
    sensors_json_raw = sensors.json()
    sensors_json = sensors_json_raw['sensors']

    for a in sensors_json:
        for k in a.keys():
            if isinstance(a[k], dict):
                a[k] = flatten(a[k])

    # Format asset list for import into runZero
    import_assets = build_assets_from_json(sensors_json)

    # Import assets into runZero
    import_data_to_runzero(assets=import_assets)

# *** Should not need to touch this ***
if __name__ == '__main__':
    main()