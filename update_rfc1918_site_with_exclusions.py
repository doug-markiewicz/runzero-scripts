'''
    The purpose of this script is to streamline configuration of an RFC1918 scan of unknown networks, excluding all known networks.

    * An oauth client ID and secret from a runZero account is needed to run this script.
    * A known network is defined as any IP or subnet defined within the site configurations for in-scope orgs.
    * This script will pull all sites within a defined org.
    * This script will check both the default scan scope and registered subnets for each site.
    * It is assumed that you are running the RFC 1918 scan in its own dedicated site.
    * It is assumed that the RFC 1918 scan task will be configured to to pull exclusions from the site exclusions list.
    * The site can be part of an existing org or a new org created specifically for this purpose.
    * This script does not account for any IPs or subnets that are defined within a specific task configuration.

    Set ORG_IDS to the list of org UUIDs that you want to pull registered subnets from. 
    Set RFC1918_ORG_ID to the org UUID that contains the RFC 1918 scan.
    Set RFC1918_SITE_ID to the site UUID of the site that the RFC 1918 scan is configured in.
'''

import requests
import os
import json
from datetime import datetime

# These can be removed if you are hard coding the org id and export token
from dotenv import load_dotenv
load_dotenv()

# Load global variables from .env file
# Alternatively you can hard code the org id and org token
RUNZERO_CLIENT_ID = os.getenv('RUNZERO_CLIENT_ID')
RUNZERO_CLIENT_SECRET = os.getenv('RUNZERO_CLIENT_SECRET')
RUNZERO_BASE_URL = 'https://console.runZero.com/api/v1.0'

# Define orgs to pull registered subnets from; all sites within the org will be included
ORG_IDS = [
    'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX',
    'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'
]

RFC1918_ORG_ID = 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'
RFC1918_SITE_ID = 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'

# Authentication with client ID and secret and obtain bearer token
def get_token():
    url = f'{RUNZERO_BASE_URL}/account/api/token'
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}
    
    response = requests.post(url, data=data, headers=headers, verify=True, auth=(RUNZERO_CLIENT_ID, RUNZERO_CLIENT_SECRET))
    
    if response.status_code != 200:
        print("Failed to obtain token from OAuth server.")
        exit(1)
    
    return response.json()['access_token']

# Get all sites for the specified organization
def get_sites(token, org_id):
    url = f'{RUNZERO_BASE_URL}/org/sites?_oid={org_id}'
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print("Failed to retrieve site data for org {org_id}.")
        exit(1)
    
    return json.loads(response.text)

def update_exclusions(token, exclusions):
    url = f'{RUNZERO_BASE_URL}/org/sites/{RFC1918_SITE_ID}?_oid={RFC1918_ORG_ID}'
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
    }
    data = {
        "excludes": ", ".join(exclusions)
    }
    
    response = requests.patch(url, headers=headers, json=data)
    
    if response.status_code != 200:
        print("Failed to update exclusions for RFC 1918 scan site.")
        exit(1)
    
    return

def main():
    token = get_token()
    registered_subnets = []

    for org in ORG_IDS:
        
        sites = get_sites(token, org)
        
        for s in sites:

            # Parse default scan scope
            scope = s.get('scope', '')
            addr_array = scope.splitlines()
            for addr in addr_array:
                registered_subnets.append(addr)
            
            # Parse registered subnets
            subnets = s.get('subnets', [])
            addr_array = list(subnets.keys()) 
            for addr in addr_array:
                registered_subnets.append(addr)
    
    update_exclusions(token, registered_subnets)
    print("Successfully updated exclusions for RFC 1918 scan site.")

if __name__ == '__main__':
    main()