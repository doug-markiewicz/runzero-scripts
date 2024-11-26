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

# Get all explorers within specified organization
def get_explorers(token, org_id):
    explorers = requests.get(f'{RUNZERO_BASE_URL}/org/explorers?_oid={org_id}', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if explorers.status_code != 200:
        print("Failed to retrieve explorer data.")
        exit(1)
    return explorers

# Get latest explorer version
def get_explorer_version():
    metadata = requests.get('https://console.runzero.com/api/v1.0/metadata')
    if metadata.status_code != 200:
        print("Unable to retrieve console metadata from https://console.runzero.com/api/v1.0/metadata.")
        exit(1)
    metadata_json = metadata.json()
    version = metadata_json.get('Version','')
    return version.lstrip('v')

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

def explorers_healthcheck():

    access_token = get_token()
    client_id = get_client_id(access_token)
    orgs = get_organizations(access_token)
    current_version = get_explorer_version()
    
    recommended_explorer_memory_GiB = 8 # Measured in GiB or Gibibytes
    recommended_explorer_memory_bytes =  recommended_explorer_memory_GiB * 2**30
    
    metric_org_count = 0
    metric_explorer_count = 0
    metric_out_of_date_explorers = 0
    metric_up_to_date_explorers = 0
    metric_online_explorers = 0
    metric_offline_explorers = 0
    metric_supports_screenshots = 0
    metric_memory_allocation = 0
    metric_passive_sampling = 0
    
    explorers_output = []

    fields = [
        "organization_name",
        "id",
        "name",
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
        demo = o.get('demo', '')
        if not demo:
            metric_org_count += 1
            org_id = o.get('id', '')
            org_name = o.get('name', '')

            explorers = (get_explorers(access_token, org_id))
            explorers_json = explorers.json()      

            for item in explorers_json:

                # Calculate explorer metrics
                metric_explorer_count += 1

                if current_version in item.get('version', ''):
                    metric_up_to_date_explorers +=1
                else:
                    metric_out_of_date_explorers += 1

                if item.get('connected', ''):
                    metric_online_explorers += 1
                else:
                    metric_offline_explorers += 1
                
                if item.get('system_info', {}).get('attributes', {}).get('CanScreenshot', '') == 'true':
                    metric_supports_screenshots += 1
                
                if item.get('system_info', {}).get('mem', {}).get('total', '') < recommended_explorer_memory_bytes:
                    metric_memory_allocation += 1

                # Check if passive sampling is configured for explorer
                explorer_id = item.get('id', '')
                passive = check_passive(access_token, explorer_id)
                if passive:
                    metric_passive_sampling += 1

                # Append explorer details to output file
                explorers_output.append({
                        'organization_name':org_name,
                        'name':item.get('name', ''),
                        'id':explorer_id,
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
        
    DATA_DIRECTORY = 'data/' + date.today().strftime("%Y%m%d") + '_' + client_id

    # Check that the data directory exists
    if not os.path.isdir('data'):
        os.mkdir('data')

    # Check that the output directory exists
    if not os.path.isdir(DATA_DIRECTORY):
        os.mkdir(DATA_DIRECTORY)

    metrics_output_file = DATA_DIRECTORY + '/metrics.txt'
    explorers_output_file = DATA_DIRECTORY + '/explorers_output.csv'

    write_to_csv(output=explorers_output, filename=explorers_output_file, fieldnames=fields)

    with open(metrics_output_file, 'a') as f:

        f.write('explorer metrics                                ' + datetime.now().strftime('%m/%d/%Y, %H:%M:%S') + '\n')
        f.write('  total explorers                               ' + str(metric_explorer_count) + ' explorers across ' + str(metric_org_count) + ' organizations.\n')
        f.write('  online explorers                              ' + str(metric_online_explorers) + '\n')
        f.write('  offline explorers                             ' + str(metric_offline_explorers) + '\n')
        f.write('  explorers running latest version              ' + str(metric_up_to_date_explorers) + '\n')
        f.write('  explorers not running latest version          ' + str(metric_out_of_date_explorers) + '\n')
        f.write('  explorers with passive sampling enabled       ' + str(metric_passive_sampling) + '\n')
        f.write('  explorers that support screenshots            ' + str(metric_supports_screenshots) + '\n')
        f.write('  explorers below recommended memory allocation ' + str(metric_memory_allocation) + '\n')
        f.write('\n')

    print('Explorer metrics appended to ' + os.getcwd() + '/' + metrics_output_file)
    print('Explorer details saved to ' + os.getcwd() + '/' + explorers_output_file)

if __name__ == '__main__':
    explorers_healthcheck()