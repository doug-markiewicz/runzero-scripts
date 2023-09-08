# runZero Python SDK script for Tanium
# Last updated 9/8/2023
# This custom integration script leverages Tanium's GraphQL API gateway, not their REST API.

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

'''   
    The following attributes need to be configured to match the account that is being queried. If you are a SaaS customer, the base url and token url
    should remain the same. If you have an on-premise deployment, then console.runzero.com will need to be updated with the console address. This 
    script uses the account API credentials for authentication. Visiting the following URL for instructions on creating account API credentials.

    https://www.runzero.com/docs/leveraging-the-api/#account-api

    If you'd like to seperate out credentials, they can be imported from a seperate file.

    Example:

    import tanium_config
    RUNZERO_CLIENT_ID = tanium_config.RUNZERO_CLIENT_ID
    RUNZERO_CLIENT_SECRET = tanium_config.RUNZERO_CLIENT_SECRET
    TANIUM_API_TOKEN = tanium_config.TANIUM_API_TOKEN
'''

# Configure runZero environment
RUNZERO_BASE_URL = 'https://console.runZero.com/api/v1.0'
RUNZERO_ORG_ID = ' '
RUNZERO_SITE_NAME = 'Tanium Unknown Assets'
RUNZERO_SITE_ID = ' '
RUNZERO_CUSTOM_SOURCE_ID = ' ' 
RUNZERO_IMPORT_TASK_NAME = 'Tanium Sync'
RUNZERO_CLIENT_ID = ' '
RUNZERO_CLIENT_SECRET = ' '

# Configure Tanium environment
TANIUM_API_GATEWAY = 'https://<you_tanium_api_gateway>/plugin/products/gateway/graphql'
TANIUM_API_TOKEN = ''

# Configure runZero variables
RUNZERO_BASE_URL = tanium_config.RUNZERO_BASE_URL
RUNZERO_ORG_ID = tanium_config.RUNZERO_ORG_ID
RUNZERO_SITE_NAME = tanium_config.RUNZERO_SITE_NAME
RUNZERO_SITE_ID = tanium_config.RUNZERO_SITE_ID
RUNZERO_CUSTOM_SOURCE_ID = tanium_config.RUNZERO_CUSTOM_SOURCE_ID
RUNZERO_IMPORT_TASK_NAME = tanium_config.RUNZERO_IMPORT_TASK_NAME
RUNZERO_CLIENT_ID = tanium_config.RUNZERO_CLIENT_ID
RUNZERO_CLIENT_SECRET = tanium_config.RUNZERO_CLIENT_SECRET

# Configure Tanium variables
TANIUM_API_GATEWAY = tanium_config.TANIUM_API_GATEWAY
TANIUM_API_TOKEN = tanium_config.TANIUM_API_TOKEN

def build_assets_from_json(json_input: List[Dict[str, Any]]) -> List[ImportAsset]:
    assets: List[ImportAsset] = []
    for i in json_input:
        item = i["node"]
        # grab known API attributes from the json dict that are always present
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

def build_network_interface(ips: List[str], mac: str = None) -> NetworkInterface:
    ''' 
    This function converts a mac and a list of strings in either ipv4 or ipv6 format and creates a NetworkInterface that
    is accepted in the ImportAsset
    '''
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


def import_data_to_runzero(assets: List[ImportAsset]):

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
                        generation
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
            variables = {"first": 1000, "after": cursor}
        else:
            variables = {"first": 1000}

        # Request batch of endpoints
        endpoints = requests.post(url=TANIUM_API_GATEWAY, headers=query_headers, json={'query': query, 'variables': variables})

        # Check for 200 OK response code and exit if error
        if endpoints.status_code != 200:
            print("Tanium Response: " + str(endpoints.status_code) + " " + endpoints.text)
            exit(endpoints.status_code)
        
        # Parse JSON object to native python object
        endpoints_json = endpoints.json()["data"]["endpoints"]["edges"]
                    
        # Extract page info from 
        hasNextPage = endpoints.json()["data"]["endpoints"]["pageInfo"]["hasNextPage"]
        startCursor = endpoints.json()["data"]["endpoints"]["pageInfo"]["startCursor"]
        endCursor = endpoints.json()["data"]["endpoints"]["pageInfo"]["endCursor"]
        print(str(datetime.now()) + f" Received data for endpoints between {startCursor} and {endCursor}")
        
        endpoint_array.extend(endpoints_json)

        # Set cursor value for next batch of endpoints
        cursor = endCursor

    # Format asset list for import into runZero
    print(str(datetime.now()) + f" Building assets for import into runZero.")
    import_assets = build_assets_from_json(endpoint_array)

    # Import assets into runZero
    print(str(datetime.now()) + f" Importing assets into runZero.")
    import_data_to_runzero(assets=import_assets)

if __name__ == '__main__':
    main()