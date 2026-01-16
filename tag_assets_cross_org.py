import requests
import os
import json
import csv
import sys
import logging

from dotenv import load_dotenv
load_dotenv()

RUNZERO_CLIENT_ID = os.getenv("RUNZERO_CLIENT_ID")
RUNZERO_CLIENT_SECRET = os.getenv("RUNZERO_CLIENT_SECRET")
RUNZERO_BASE_URL = 'https://console.runzero.com/api/v1.0'

''' 
Set CSV_FILE to the location of the file you want to read in.
Set CSV_COLUMN to the column where the IP address is located. Column A is 0. 
Set CSV_HEADER to True if your CSV file contains a header row or False is no header.
'''
CSV_FILE = 'tag_assets_cross_org.csv'
CSV_COLUMN = 0
CSV_HEADER = True

# Set tag to apply to all assets discovered in CSV_FILE
TAG = 'INFRA'

# Path to the list of IPs that were not found and tagged
OUTPUT_FILE = 'tag_assets_cross_org.log'

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(OUTPUT_FILE, mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Authenticate with client ID and secret and obtain bearer token
def get_token():
    url = f'{RUNZERO_BASE_URL}/account/api/token'
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, headers=headers, verify=True, data=data, auth=(RUNZERO_CLIENT_ID, RUNZERO_CLIENT_SECRET))
    if response.status_code != 200:
        logging.error('Failed to obtain token from OAuth server. Status code ' + token_response.status_code + '.')
        logging.error(response.text)
        exit(1)
    token_json = json.loads(response.text)
    return token_json['access_token']   

# Fetch organizations from account
def get_organizations(token):
    url = f'{RUNZERO_BASE_URL}/account/orgs'
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + token}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.error('Failed to retrieve organization data. Status code ' + response.status_code + '.')
        logging.error(response.text)
        exit(1)
    elif len(json.loads(response.text)) < 1:
        logging.error('Something went wrong. The provided token did not return any organizations.')
    else: 
        return json.loads(response.text)

# Fetch assets from organization
def get_assets(token, org_id):
    fields = 'id,addresses'
    url = f'{RUNZERO_BASE_URL}/org/assets?_oid={org_id}&fields={fields}'
    headers = headers={"Content-Type": "application/json", "Authorization": "Bearer " + token}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.error('Failed to retrieve asset data. Status code ' + assets.status_code + '.')
        logging.error(response.text)
        exit(1)
    return response

def tag_asset(token, org_id, uuid):
    url = f'{RUNZERO_BASE_URL}/org/assets/{uuid}/tags?_oid={org_id}'
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + token}
    data = {"tags": TAG}
    response = requests.patch(url, headers=headers, json=data)
    if response.status_code != 200:
        logging.error('Failed to tag asset ' + uuid + ' in org_id ' + org_id + '. Status code ' + str(response.status_code) + '.')
        logging.error(response.text)
        exit(1)
    return

def main():

    addr_list = []
    addr_not_found_list = []

    # Read CSV file
    with open(CSV_FILE, 'r') as csvfile:
        reader = csv.reader(csvfile)

        if CSV_HEADER == True:
            next(reader)

        for r in reader:
            if r:
                addr_list.append(r[CSV_COLUMN])

    # Add all addresses to not found list. Addresses will be removed as they are discovered.
    addr_not_found_list = addr_list.copy()

    bearer_token = get_token()
    orgs = get_organizations(bearer_token)

    # Loop through organizations and search for assets to tag
    for o in orgs:
        org_id = o.get('id', '')
        org_name = o.get('name', '')
        logging.info('Fetching assets from ' + org_name + ' (' + org_id + ').')
        assets = get_assets(bearer_token, org_id)
        assets_json = assets.json()

        # Loop through assets and tag ones that are found in addr_list
        asset_counter = 0
        tag_counter = 0
        for a in assets_json:
            uuid = a.get('id', '')
            addresses = a.get('addresses', [])
            if addresses:
                for addr in addresses:
                    if addr in addr_list:
                        tag_asset(bearer_token, org_id, uuid)
                        if addr in addr_not_found_list:
                            addr_not_found_list.remove(addr)
                        tag_counter += 1
            asset_counter += 1      
        logging.info('Tagged ' + str(tag_counter) + ' of ' + str(asset_counter) + ' assets in ' + org_name + ' (' + org_id + ').')
  
    # Write list of addresses that were not found
    if addr_not_found_list:
        logging.warning('One or more addresses were not found in inventory. ')
        logging.warning(addr_not_found_list)

if __name__ == '__main__':
    main()