import requests
import os
import uuid
import json
import datetime
from flatten_json import flatten
from ipaddress import ip_address
from typing import Any, Dict, List

import runzero
from runzero.client import AuthError
from runzero.api import CustomAssets, Sites
from runzero.types import (CustomAttribute,ImportAsset,IPv4Address,IPv6Address,NetworkInterface,ImportTask)

# Configure runZero variables
RUNZERO_BASE_URL = 'https://console.runZero.com/api/v1.0'
RUNZERO_ORG_ID = ''
RUNZERO_SITE_NAME = ''
RUNZERO_SITE_ID = ''
RUNZERO_CUSTOM_SOURCE_ID = '' 
RUNZERO_IMPORT_TASK_NAME = 'Tanium Sync'
RUNZERO_CLIENT_ID = ''
RUNZERO_CLIENT_SECRET = ''

# Configure Tanium variables
TANIUM_API_GATEWAY = 'https://your-account-api.cloud.tanium.com/plugin/products/gateway/graphql'
TANIUM_API_TOKEN = 'token-1234567890abcdefghijklmnopqrstuvwxyz'

def build_assets_from_json(json_input: List[Dict[str, Any]]) -> List[ImportAsset]:
    '''
    This is an example function to highlight how to handle converting data from an API into the ImportAsset format that
    is required for uploading to the runZero platform. This function assumes that the json has been converted into a list 
    of dictionaries using `json.loads()` (or any similar functions).
    '''

    assets: List[ImportAsset] = []
    for i in json_input:
        item = i["node"]
        # grab known API attributes from the json dict that are always present
        tanium_oid = item.get('id', uuid.uuid4)
        tanium_hostname = item.get('name', '')
        tanium_mac = item.get('macAddresses_0', '')
        tanium_address = item.get('ipAddress', '')
        tanium_domain = item.get('domainName', '')
        tanium_first_seen = item.get('eidFirstSeen', '')
        tanium_last_seen = item.get('eidLastSeen', '')
        tanium_os_name = item.get('os_name', '')
        tanium_manufacturer = item.get('manufacturer', '')
        tanium_model = item.get('model', '')

        # create the network interface
        network = build_network_interface(ips=[tanium_address], mac=tanium_mac)
        print(network)

        # *** DO NOT TOUCH ***
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
                id=tanium_oid,
                networkInterfaces=[network],
                hostnames=[tanium_hostname],
                domain=tanium_domain,
                os=tanium_os_name,
                first_seen_ts=tanium_first_seen,
                last_seen_ts=tanium_last_seen,
                manufacturer=tanium_manufacturer,
                model=tanium_model,
                customAttributes=custom_attrs
            )
        )
    return assets

# *** DO NOT TOUCH ***
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
    # Check for custom source and create new one if it doesn't exist
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

    # Set Tanium GraphQL query 
    query = """query getEndpoints($first: Int, $after: Cursor) {
        endpoints(first: $first, after: $after) {
            edges {
                node {
                    id
                    computerID
                    systemUUID
                    name
                    ipAddress
                    domainName
                    macAddresses
                    os {
                        name
                    }
                    model
                    manufacturer
                    serialNumber
                    eidFirstSeen
                    eidLastSeen
                    lastLoggedInUser
                    isEncrypted     

                }
            }
            pageInfo {
                hasNextPage
                endCursor
                startCursor
            }
        }
    }"""

    # Set HTTP headers
    query_headers = {"Content-Type": "application/json","session": TANIUM_API_TOKEN}

    cursor = None
    hasNextPage = True
    endpoint_array = []

    while hasNextPage:

        # Set query variables
        if cursor:
            variables = {"first": 100, "after": cursor}
        else:
            variables = {"first": 100}

        # Request batch of endpoints
        endpoints = requests.post(url=TANIUM_API_GATEWAY, headers=query_headers, json={'query': query, 'variables': variables})

        # Check for 200 OK response code and exit if error
        if endpoints.status_code != 200:
            print("Response: " + str(endpoints.status_code) + " " + endpoints.text)
            exit(endpoints.status_code)
        
        # Parse JSON object to native python object
        endpoints_json = endpoints.json()["data"]["endpoints"]["edges"]
        
        # Print endpoints for troubleshooting
        #print(json.dumps(endpoints.json(),indent=2))

        for a in endpoints_json:
            for k in a.keys():
                if isinstance(a[k], dict):
                    a[k] = flatten(a[k])

        # Extract page info from 
        hasNextPage = endpoints.json()["data"]["endpoints"]["pageInfo"]["hasNextPage"]
        startCursor = endpoints.json()["data"]["endpoints"]["pageInfo"]["startCursor"]
        endCursor = endpoints.json()["data"]["endpoints"]["pageInfo"]["endCursor"]
        print(str(datetime.datetime.now()) + f" Received data for endpoints between {startCursor} and {endCursor}")
        
        endpoint_array.extend(endpoints_json)

        # Set cursor value for next batch of endpoints
        cursor = endCursor

    # Format asset list for import into runZero
    print(str(datetime.datetime.now()) + f" Building assets for import into runZero.")
    import_assets = build_assets_from_json(endpoint_array)

    # Import assets into runZero
    print(str(datetime.datetime.now()) + f" Importing assets into runZero.")
    import_data_to_runzero(assets=import_assets)

# *** DO NOT TOUCH ***
if __name__ == '__main__':
    main()