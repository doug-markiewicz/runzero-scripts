# runZero Custom Integration with LimaCharlie
# Docs: https://www.runzero.com/docs/integrations-inbound/
# Docs: https://pypi.org/project/runzero-sdk/ 
# Docs: https://doc.limacharlie.io/docs/documentation/dec140b42ad78-api-keys
# Docs: https://doc.limacharlie.io/docs/api/43897cbb915ef-lima-charlie-io-rest-api
# Prerequisite: pip install runzero-sdk

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

# Configure runZero variables
# Script uses pipenv, but os.environ[] can be swapped out for a hardcoded value to make testing easier
RUNZERO_BASE_URL = 'https://console.runZero.com/api/v1.0'
RUNZERO_CLIENT_ID = os.environ['RUNZERO_CLIENT_ID']
RUNZERO_CLIENT_SECRET = os.environ['RUNZERO_CLIENT_SECRET']
RUNZERO_API_TOKEN = os.environ['RUNZERO_API_TOKEN']
RUNZERO_ORG_ID = '98828456-f9ee-485d-aff6-11ddc91b2468'
RUNZERO_CUSTOM_SOURCE_ID = 'cc000d15-0918-4803-80d6-9e86bf6c4dcb' 
RUNZERO_SITE_NAME = 'LimaCharlie New Assets'
RUNZERO_SITE_ID = '9914eac7-9899-49cd-a426-d73a98799663'
RUNZERO_IMPORT_TASK_NAME = 'LimaCharlie Sync'
RUNZERO_HEADER = {'Authorization': f'Bearer {RUNZERO_API_TOKEN}'}

# Configure LimaCharlie variables
# Script uses pipenv, but os.environ[] can be swapped out for a hardcoded value to make testing easier
LIMACHARLIE_JWT_URL = 'https://jwt.limacharlie.io/'
LIMACHARLIE_BASE_URL = 'https://api.limacharlie.io/v1'
LIMACHARLIE_OID = os.environ['LIMACHARLIE_OID']
LIMACHARLIE_SECRET = os.environ['LIMACHARLIE_SECRET']

def build_assets_from_json(json_input: List[Dict[str, Any]]) -> List[ImportAsset]:
    '''
    This is an example function to highlight how to handle converting data from an API into the ImportAsset format that
    is required for uploading to the runZero platform. This function assumes that the json has been converted into a list 
    of dictionaries using `json.loads()` (or any similar functions).
    '''

    assets: List[ImportAsset] = []
    for item in json_input:
        # grab known API attributes from the json dict that are always present
        sensor_oid = item.get('oid', uuid.uuid4)
        sensor_hostname = item.get('hostname', '')
        sensor_mac = item.get('mac_addr', [])
        sensor_int_ip = item.get('int_ip', '')

        # if multiple mac addresses, take the first one
        if len(sensor_mac) > 0:
           mac = sensor_mac[0].replace('-', ':')
        else:
           mac = None

        # create the network interface
        network = build_network_interface(ips=[sensor_int_ip], mac=sensor_mac)

        # *** Should not need to touch this ***
        # handle any additional values and insert into custom_attrs
        custom_attrs: Dict[str, CustomAttribute] = {}
        for key, value in item.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    custom_attrs[k] = CustomAttribute(str(v)[:1023])
            else:
               custom_attrs[key] = CustomAttribute(str(value))

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


    # (Optional)
    # Check for custom integration source in runZero and create new one if it doesn't exist
    # You can create one manually within the UI and hardcode RUNZERO_CUSTOM_SOURCE_ID
    '''
    custom_source_mgr = CustomSourcesAdmin(c)
    my_asset_source = custom_source_mgr.get(name='fortiedr')
    if my_asset_source:
        source_id = my_asset_source.id
    else:
        my_asset_source = custom_source_mgr.create(name='fortiedr')
        source_id = my_asset_source.id
    '''

    # create the import manager to upload custom assets
    import_mgr = CustomAssets(c)
    import_task = import_mgr.upload_assets(org_id=RUNZERO_ORG_ID, site_id=RUNZERO_SITE_ID, custom_integration_id=RUNZERO_CUSTOM_SOURCE_ID, assets=assets, task_info=ImportTask(name=RUNZERO_IMPORT_TASK_NAME))

    if import_task:
        print(f'task created! view status here: https://console.runzero.com/tasks?task={import_task.id}')


def main():

    # Build JWT request URL
    jwt_url = f'{LIMACHARLIE_JWT_URL}?oid={LIMACHARLIE_OID}&secret={LIMACHARLIE_SECRET}'

    # Request JWT
    jwt = requests.post(jwt_url, '')

    # Parse JSON object to native python object
    token = jwt.json()

    # Request sensor list
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