# create_custom_assets.py
#
# This script leverages runZero's custom integration API to create assets from a .csv file. It is intended
# for a one time upload. Running this script on the same set of assets more than once will create 
# duplicate asset records. The PATCH endpoint should be used for updating existing assets.
#
# Instructions:
#     1) Define custom integration in runZero
#     2) Set global variables for script 
#     3) Create a CSV file of the assets you want to upload to runZero
#     4) Update CSV file location in script    
#     5) Update build_asset() to map appropriate attributes from .csv file to rZ attributes.
#        (See create_custom_assets_sample_format.json for example)
#
# Notes
#     - Running this script on the same set of assets more than once will create duplicate asset records. The PATCH endpoint should be used for updating existing assets.
#     - Custom attributes cannot be named after reserved attribute names used by runZero or they will be dropped during creation.
#
import uuid
import requests
import os
import json
import csv
import datetime
from dotenv import load_dotenv
from typing import Any, Dict, List

load_dotenv()
RUNZERO_ORG_ID = os.getenv('RUNZERO_ORG_ID')
RUNZERO_SITE_ID = os.getenv('RUNZERO_SITE_ID')
RUNZERO_CUSTOM_INT_ID = os.getenv('RUNZERO_CUSTOM_INT_ID')
RUNZERO_TOKEN = os.getenv('RUNZERO_TOKEN')
RUNZERO_BASE_URL = 'https://console.runZero.com/api/v1.0'
CSV_FILE = '/Users/doug/Documents/Projects/runzero-scripts/create_custom_assets.csv'

# Convert csv asset record to json asset record
def build_asset(asset):
    now = int(datetime.datetime.now().strftime('%s'))
    asset_record = {
        "asset": {
            "id": str(uuid.uuid4()),
            "hostnames": [
                asset['hostname']
            ],
            "domains": [
                asset['domain']
            ],
            "addresses": [
                asset['address']
            ],
            "macs": [
                asset['mac']
            ],            
            "os": asset['os'],
            "hw": asset['hw'],
            "device_type": asset['type'],
            "first_seen": now,
            "comments": asset['comments']
        }
    }
    return asset_record

def main():
    # Set parameters for POST
    url = f'{RUNZERO_BASE_URL}/org/custom-integrations/{RUNZERO_CUSTOM_INT_ID}/asset?_oid={RUNZERO_ORG_ID}&site={RUNZERO_SITE_ID}'
    header = {"Content-Type": "application/json", "Authorization": "Bearer " + RUNZERO_TOKEN}
    
    # Read .csv file and create assets in runZero
    with open(CSV_FILE, 'r') as data:
        for a in csv.DictReader(data):
            asset = build_asset(a)
            response = requests.post(url, json=asset, headers=header)
            if response.status_code == 200:
                print('successfully uploaded asset to runZero:', response.json())
            else:
                print('failed to upload assets to runZero', response.json())
                exit(1)

if __name__ == '__main__':
    main()