import requests
import os
import json
import csv
from datetime import datetime

# these can be removed if you are hard coding the org id and export token
from dotenv import load_dotenv
load_dotenv()

# load global variables from .env file
# alternatively you can hard code the org id and org token
RUNZERO_ORG_ID = os.getenv('RUNZERO_ORG_ID')
RUNZERO_ORG_TOKEN = os.getenv('RUNZERO_ORG_TOKEN')
RUNZERO_BASE_URL = 'https://console.runZero.com/api/v1.0'

# define query for assets to be deleted; this should match a valid query within the platform
# sample asset query looks for all desktops and laptops seen within the last 30 days
QUERY = 'last_seen:<30d and (type:desktop or type:laptop)'

# define fields to be retrieved; in this case we only need the asset UUIDs
FIELDS = 'id'

# Fetch asset UUIDS matching defined query
def fetch_asset_uuids(query):
    asset_uuids = []
    url = f"{RUNZERO_BASE_URL}/org/assets?_oid={RUNZERO_ORG_ID}&search={query}&fields={FIELDS}"
    headers = {
        'Authorization': f"Bearer {RUNZERO_ORG_TOKEN}",
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers, timeout=600)
    if response.status_code != 200:
        print(f"Error fetching assets: {response.status_code} {response.text}")
        exit(1)
    
    assets_json  = response.json()

    for a in assets_json:
        asset_uuids.append(a['id'])
    
    return asset_uuids

# Bulk delete assets matching list of UUIDs
def delete_assets(asset_uuids):
    url = f"{RUNZERO_BASE_URL}/org/assets/bulk/delete?_oid={RUNZERO_ORG_ID}"
    headers = {
        'Authorization': f"Bearer {RUNZERO_ORG_TOKEN}",
        'Content-Type': 'application/json'
    }

    batch_size = 1000
    total_assets = len(asset_uuids)

    for a in range(0, total_assets, batch_size):
        batch_uuids = asset_uuids[a:a + batch_size]
        data = {
            "asset_ids": batch_uuids
        }
        response = requests.post(url, headers=headers, json=data, timeout=600)
        if response.status_code == 204:
            print(f"Successfully deleted batch of {len(batch_uuids)} assets.")
        else:
            print(f"Error deleting assets: {response.status_code} {response.text}")
    return

def main():

    # Fetch list of UUIDs for assets matching the query
    asset_uuids = fetch_asset_uuids(QUERY)
    count = len(asset_uuids)
    
    if count == 0:
        print("No assets found matching the query. Exiting.")
        return
    
    print(f"Found {count} assets matching the query: {QUERY}.")
    
    # Confirm before proceeding with deletion
    confirm = input(f"Do you wish to proceed with deleting {count} assets? (y/n): ").lower().strip()

    if confirm == 'y':
        print("Deleting assets...")
        delete_assets(asset_uuids)
        return
    elif confirm == 'n':
        print("Exiting without deleting assets.")
        return
    else:
        print("Invalid input. Exiting without deleting assets.")
        return
    
if __name__ == '__main__':
    main()