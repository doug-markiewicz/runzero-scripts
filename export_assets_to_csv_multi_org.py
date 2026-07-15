import requests
import os
import json
import csv
from datetime import datetime

# these can be removed if you are hard coding the client id and client secret
from dotenv import load_dotenv
load_dotenv()

# load global variables from .env file
# alternatively you can hard code the org id and export token
RUNZERO_CLIENT_ID = os.getenv("RUNZERO_CLIENT_ID")
RUNZERO_CLIENT_SECRET = os.getenv("RUNZERO_CLIENT_SECRET")
RUNZERO_BASE_URL = 'https://console.runZero.com/api/v1.0'

# set the path of export files
CSV_FILE_PATH = '/Users/doug/Downloads/'

# define runzero asset query; this should match a valid query within the platform
# leave blank to export all assets, or define a query to filter the results
# sample query: last_seen:<30days and (type:desktop or type:laptop or type:server)
QUERY = ''

# Fetch token from runZero OAuth server using client credentials
def get_token():
    url = f'{RUNZERO_BASE_URL}/account/api/token'
    header = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, data=data, headers=header, verify=True, auth=(RUNZERO_CLIENT_ID, RUNZERO_CLIENT_SECRET))
    if response.status_code != 200:
        print("Failed to obtain token from OAuth server.")
        exit(1)
    else:
        token_json = json.loads(response.text)
        return token_json['access_token']

# Fetch all organization IDs associated with the account token
def get_org_ids(token):
    url = f'{RUNZERO_BASE_URL}/account/orgs'
    header = {"Content-Type": "application/json", "Authorization": "Bearer " + token}
    response = requests.get(url, headers=header)
    if response.status_code != 200:
        print('Failed to fetch org IDs from ' + url)
        exit(1)
    orgs = response.json()
    org_info = [{"id": org["id"], "name": org.get("name", "")} for org in orgs]
    return org_info

# Fetch assets in CSV format for specified organization ID
def get_assets_csv(token, org_id):
    url = f'{RUNZERO_BASE_URL}/export/org/assets.csv?_oid={org_id}&search={QUERY}'
    header = {"Content-Type": "application/json", "Authorization": "Bearer " + token}
    response = requests.get(url, headers=header)
    if response.status_code != 200:
        print('Failed to export assets from ' + url)
        exit(1)
    return response.content

def main():
    token = get_token()
    orgs = get_org_ids(token)
    for org in orgs:
        org_id = org['id']
        org_name = org['name']
        print(datetime.now().strftime('%Y%m%d %H:%M:%S ') + f'exporting assets for org ID: {org_id}, org name: {org_name}')
        assets_csv = get_assets_csv(token, org_id)
        with open(os.path.join(CSV_FILE_PATH, f'export_assets_{org_id}_{org_name}.csv'), 'wb') as f:
            print(datetime.now().strftime('%Y%m%d %H:%M:%S ') + f'saving assets to {os.path.join(CSV_FILE_PATH, f"export_assets_{org_id}_{org_name}.csv")}')
            f.write(assets_csv)

if __name__ == '__main__':
    main()