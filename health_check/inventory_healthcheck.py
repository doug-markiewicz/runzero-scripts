from dotenv import load_dotenv
import os
import requests
import json
import csv
from datetime import datetime, date
from typing import Any, Dict, List
from urllib.parse import quote

load_dotenv()
RUNZERO_BASE_URL = os.getenv("RUNZERO_BASE_URL")
RUNZERO_CLIENT_ID = os.getenv("RUNZERO_CLIENT_ID")
RUNZERO_CLIENT_SECRET = os.getenv("RUNZERO_CLIENT_SECRET")

# Authentication with client ID and secret and obtain bearer token
def get_token():
    token_request_url = f'{RUNZERO_BASE_URL}/account/api/token'
    token_request_header = {"Content-Type": "application/x-www-form-urlencoded"}
    token_request_data = {"grant_type": "client_credentials"}
    token_response = requests.post(token_request_url, data=token_request_data, headers=token_request_header, verify=True, auth=(RUNZERO_CLIENT_ID, RUNZERO_CLIENT_SECRET))
    if token_response.status_code != 200:
        print("Failed to obtain token from OAuth server.")
        exit(1)
    else:
        token_json = json.loads(token_response.text)
        return token_json['access_token']    
    
# Get client-id
def get_client_id(token):
    account = requests.get(f'{RUNZERO_BASE_URL}/account/orgs', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if account.status_code != 200:
        print("Failed to retrieve account information.")
        exit(1)
    account_json = account.json()
    return account_json[0].get('client_id','')

# Get all organization within defined account
def get_organizations(token):
    orgs = requests.get(f'{RUNZERO_BASE_URL}/account/orgs', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if orgs.status_code != 200:
        print("Failed to retrieve organization data.")
        exit(1)
    return json.loads(orgs.text)

def get_assets(token, org_id):
    if type == 'recurring':
        search = quote('recur:=true')
        tasks = requests.get(f'{RUNZERO_BASE_URL}/account/tasks?search={search}', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    else:
        search = quote('created_at:<90days and not type:analysis and recur:=false')
        tasks = requests.get(f'{RUNZERO_BASE_URL}/account/tasks?search={search}', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})

    if tasks.status_code != 200:
        print("Failed to retrieve task data.")
        exit(1)
    return tasks

def inventory_healthcheck():

    access_token = get_token()
    client_id = get_client_id(access_token)
    orgs = get_organizations(access_token)

    metric_total_recent_assets = 0
    metric_total_recent_live_assets = 0
    metric_assets_missing_os = 0
    metric_assets_missing_mac = 0
    metric_assets_missing_hostname = 0
    metric_duplicate_assets_by_hostname_mac = 0

    for o in orgs:
        demo = o.get('demo', '')
        if not demo:
            org_id = o.get('id', '')
            assets = get_assets(access_token, org_id)
            print(assets.status_code)
    
    DATA_DIRECTORY = 'data/' + date.today().strftime("%Y%m%d") + '_' + client_id

    # Check that the data directory exists
    if not os.path.isdir('data'):
        os.mkdir('data')

    # Check that the output directory exists
    if not os.path.isdir(DATA_DIRECTORY):
        os.mkdir(DATA_DIRECTORY)

    metrics_output_file = DATA_DIRECTORY + '/metrics.txt'


if __name__ == '__main__':
    inventory_healthcheck()