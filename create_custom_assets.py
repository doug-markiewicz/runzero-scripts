# create_custom_assets.py
#
# This script leverages runZero's custom integration API to create assets from a .csv file. It is intended
# for a one time upload. Running this script on the same set of assets more than once will create 
# duplicate asset records. The PATCH endpoint should be used for updating existing assets.
#
# Instructions:
#     1) Define custom integration in runZero
#     2) Set relevant variables in main(). These can also be entered at runtime. 
#     3) Update build_asset() to map appropriate attributes from .csv file to rZ attributes.
#        (See create_custom_assets_sample_format.json for example)
#
# Notes
#     - Running this script on the same set of assets more than once will create duplicate asset records. The PATCH endpoint should be used for updating existing assets.
#     - Custom attributes cannot be named after reserved attribute names used by runZero or they will be dropped during creation.
#
# run python3 create_custom_assets.py --help for syntax.
#
import argparse
import textwrap
import getpass
import uuid
import requests
import os
import json
import csv
from datetime import datetime, date
from flatten_json import flatten
from typing import Any, Dict, List
from runzero.client import AuthError
from runzero.api import CustomAssets, Sites
from runzero.types import (CustomAttribute,ImportAsset,IPv4Address,IPv6Address,NetworkInterface,ImportTask)

def parse_args():
    parser = argparse.ArgumentParser(
        prog='upload_assets',
        description='Upload assets from a .csv file into runZero using the custom integration API endpoint.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=True,
        epilog=textwrap.dedent('''
            Arguments specified at runtime will override any configured variables within the script.
            
            Example:  python3 upload_assets.py --org 1ae9ae03-bdbd-49d2-a06c-9c27651583e9 --site 65c292c6-705e-41f2-be92-2bb008ac376f --token OT95481E8B5E52700EA7CA5BE4BE1D assets.csv
                               
        ''')
    )
    parser.add_argument('filename')
    parser.add_argument('--org', dest='org', metavar='', help='specify the UUID of the organization where assets will be uploaded')
    parser.add_argument('--site', dest='site', metavar='', help='specify the UUID of the site where assets will be uploaded')
    parser.add_argument('--custom', dest='custom', metavar='', help='specify the UUID of the custom integration defined for assets')
    parser.add_argument('--token', dest='token', metavar='', help='specifiy the organization API token')
    return parser.parse_args()

def build_asset(asset_dict):
    asset = {
        "asset": {
            "id": str(uuid.uuid4()),
            "hostnames": [
                asset_dict['serial_number']
            ],
            "name": asset_dict['serial_number'],
            "hw": asset_dict['vendor'],
            "device_type": "Monitor",
            "custom_attributes": asset_dict
        }
    }
    return asset

def main():

    #Define optional variables
    RUNZERO_ORG_ID = ''
    RUNZERO_SITE_ID = ''
    RUNZERO_CUSTOM_INT_ID = ''
    RUNZERO_TOKEN = ''   
    RUNZERO_BASE_URL = 'console.runzero.com' 

    # Parse arguments from script execution
    args = parse_args()

    # Check for organization ID and prompt if it doesn't exist 
    try: RUNZERO_ORG_ID 
    except NameError: RUNZERO_ORG_ID = None

    if args.org != None:
        org = args.org
    elif RUNZERO_ORG_ID != None and RUNZERO_ORG_ID != '':
        org = RUNZERO_ORG_ID
    else:
        org = input('Enter organization UUID: ')

    # Check for site ID and prompt if it doesn't exist
    try: RUNZERO_SITE_ID
    except NameError: RUNZERO_SITE_ID = None

    if args.site != None:
        site = args.site
    elif RUNZERO_SITE_ID != None and RUNZERO_SITE_ID != '':
        site = RUNZERO_SITE_ID
    else:
        site = input('Enter site UUID: ')

    # Check for custom integration ID and prompt if it doesn't exist
    try: RUNZERO_CUSTOM_INT_ID
    except NameError: RUNZERO_CUSTOM_INT_ID = None

    if args.custom != None:
        custom = args.custom
    elif RUNZERO_CUSTOM_INT_ID != None and RUNZERO_CUSTOM_INT_ID != '':
        custom = RUNZERO_CUSTOM_INT_ID
    else:
        custom = input('Enter custom integration UUID: ')

    # Check for organization API token and prompt if it doesn't exist
    try: RUNZERO_TOKEN
    except NameError: RUNZERO_TOKEN = None

    if args.token != None:
        token = args.token
    elif RUNZERO_TOKEN != None and RUNZERO_TOKEN != '':
        token = RUNZERO_TOKEN
    else:
        #token = getpass.getpass(prompt='Enter organization token: ')
        token = input('Enter organization API token: ')

    # Read .csv file and create assets in runZero
    url = f'https://{RUNZERO_BASE_URL}/api/v1.0/org/custom-integrations/{custom}/asset?_oid={org}&site={site}'

    with open(args.filename, 'r') as data:
        for line in csv.DictReader(data):
            asset = build_asset(line)

            response = requests.post(url, json=asset, headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
        
            if response.status_code == 200:
                print('successfully uploaded asset to runZero:', response.json())
            else:
                print('failed to upload assets to runZero', response.json())
                exit(1)

if __name__ == '__main__':
    main()