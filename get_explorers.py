from dotenv import load_dotenv
import os
import requests
import json
import csv
from datetime import datetime, date

load_dotenv()
RUNZERO_CLIENT_ID = os.getenv("RUNZERO_CLIENT_ID")
RUNZERO_CLIENT_SECRET = os.getenv("RUNZERO_CLIENT_SECRET")
RUNZERO_BASE_URL = 'https://console.runzero.com/api/v1.0'

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

# Get all organization within defined account
def get_organizations(token):
    orgs = requests.get(f'{RUNZERO_BASE_URL}/account/orgs', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if orgs.status_code != 200:
        print("Failed to retrieve organization data.")
        exit(1)
    return json.loads(orgs.text)

# Get all explorers within specified organization
def get_explorers(token, org_id):
    explorers = requests.get(f'{RUNZERO_BASE_URL}/org/explorers?_oid={org_id}', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if explorers.status_code != 200:
        print("Failed to retrieve explorer data.")
        exit(1)
    return explorers

# Determine whether an explorer has passive sampling enabled
def check_passive(token, agent_id):
    tasks = requests.get(f'{RUNZERO_BASE_URL}/account/tasks?search=agent_id%3A{agent_id}%20and%20type%3Asample', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    
    if tasks.status_code != 200:
        print('Failed to retrieve task data and confirm whether passive sampling is configure on explorer ' + agent_id + '.')
        exit(1)
    tasks_json = tasks.json()
    if len(tasks_json) == 0:
        return False
    else:
        return True

# Output final results to a csv file
def write_to_csv(output: list, filename: str, fieldnames: list):
    file = open(filename, "w")
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output)
    file.close()

def main():
    access_token = get_token()
    orgs = get_organizations(access_token)
    
    explorers_output = []
    explorer_fields = [
        "organization_name",
        "explorer_id",
        "explorer_name",
        "last_checkin",
        "arch",
        "os",
        "version",
        "path",
        "external_ip",
        "internal_ip",
        "passive_sampling",
        "max_concurrent_scans",
        "attributes_CanScreenshot",
        "connected",
        "inactive",
        "mem_total",
        "mem_usedPercent"
    ]

    for o in orgs:
        org_id = o.get('id', '')
        org_name = o.get('name', '')

        explorers = (get_explorers(access_token, org_id))
        explorers_json = explorers.json()      

        for item in explorers_json:

            # Check if passive sampling is configured for explorer
            explorer_id = item.get('id', '')
            passive = check_passive(access_token, explorer_id)

            # Append explorer details to output file
            explorers_output.append({
                    'organization_name':org_name,
                    'explorer_name':item.get('name', ''),
                    'explorer_id':explorer_id,
                    'last_checkin':item.get('last_checkin', ''),
                    'last_checkin':datetime.fromtimestamp(item.get('last_checkin', '')).strftime('%Y-%m-%d %H:%M:%S'), # Converts epoch to readable date time format
                    'arch':item.get('arch', ''),
                    'os':item.get('os',''),
                    'version':item.get('version', ''),
                    'path':item.get('system_info', {}).get('path', ''),
                    'external_ip':item.get('external_ip', ''),
                    'internal_ip':item.get('internal_ip', ''),
                    'passive_sampling':passive,
                    'max_concurrent_scans':item.get('settings', {}).get('max_concurrent_scans', ''),
                    'attributes_CanScreenshot':item.get('system_info', {}).get('attributes', {}).get('CanScreenshot', ''),
                    'connected':item.get('connected', ''),
                    'inactive':item.get('inactive', ''),
                    'mem_total':item.get('system_info', {}).get('mem', {}).get('total', ''),
                    'mem_usedPercent':item.get('system_info', {}).get('mem', {}).get('usedPercent', '')
            })

    write_to_csv(output=explorers_output, filename="get_explorers_output.csv", fieldnames=explorer_fields)

if __name__ == '__main__':
    main()