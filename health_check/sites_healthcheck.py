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

# Get client id
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

def get_sites(token, org_id):
    sites = requests.get(f'{RUNZERO_BASE_URL}/org/sites?_oid={org_id}', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if sites.status_code != 200:
        print("Failed to retrieve site data.")
        exit(1)
    return sites

def export_sites(token, org_id):
    export = requests.get(f'{RUNZERO_BASE_URL}/export/org/sites.csv?_oid={org_id}', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if export.status_code != 200:
        print("Failed to retrieve site export csv.")
        exit(1)
    return export

# Output final results to a csv file
def write_to_csv(output: list, filename: str, fieldnames: list):
    file = open(filename, "w")
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output)
    file.close()

def sites_healthcheck():
    access_token = get_token()
    client_id = get_client_id(access_token)
    orgs = get_organizations(access_token)
    
    metric_org_count = 0
    metric_site_count = 0
    metric_total_registered_subnets_count = 0

    DATA_DIRECTORY = 'data/' + date.today().strftime("%Y%m%d") + '_' + client_id

    # Check that the data directory exists
    if not os.path.isdir('data'):
        os.mkdir('data')

    # Check that the output directory exists
    if not os.path.isdir(DATA_DIRECTORY):
        os.mkdir(DATA_DIRECTORY)

    metrics_output_file = DATA_DIRECTORY + '/metrics.txt'

    with open(metrics_output_file, 'a') as f:
        f.write('site metrics\n')
        for o in orgs:
            metric_org_count += 1
            demo = o.get('demo', '')
            if not demo:
                metric_org_count += 1
                org_id = o.get('id', '')
                org_name = o.get('name', '')
    
                # Export sites csv
                sites_export_file_path = DATA_DIRECTORY + '/sites_' + org_id + '_' + org_name + '.csv'
                sites_csv = export_sites(access_token, org_id)
                with open(sites_export_file_path, 'wb') as csv:
                    csv.write(sites_csv.content)

                # Collect site metrics
                sites = get_sites(access_token, org_id)
                sites_json = sites.json()      

                for item in sites_json:
                    metric_site_count += 1
                    site_id = item.get('id', '')
                    site_name = item.get('name', '')
                    f.write('  ' + org_name + ':' + site_name + '\n')
                    f.write('    total asset count                            : ' + str(item.get('asset_count', '')) + '\n')
                    f.write('    recent asset count                           : ' + str(item.get('recent_asset_count', '')) + '\n')
                    f.write('    live asset count                             : ' + str(item.get('live_asset_count', '')) + '\n')
                    f.write('    service count                                : ' + str(item.get('service_count', '')) + '\n')
                    f.write('    service count_tcp                            : ' + str(item.get('service_count_tcp', '')) + '\n')
                    f.write('    service count_udp                            : ' + str(item.get('service_count_udp', '')) + '\n')
                    f.write('    service count_arp                            : ' + str(item.get('service_count_arp', '')) + '\n')
                    f.write('    service count_icmp                           : ' + str(item.get('service_count_icmp', '')) + '\n')
                    f.write('    software count                               : ' + str(item.get('software_count', '')) + '\n')
                    f.write('    vulnerability count                          : ' + str(item.get('vulnerability_count', '')) + '\n')

                    metric_site_registered_subnets_count = 0
                    subnets = item.get('subnets', {})
                    if subnets:
                        for s in subnets:
                            metric_site_registered_subnets_count += 1
                            metric_total_registered_subnets_count += 1
                    
                    f.write('    registered subnets                           : ' + str(metric_site_registered_subnets_count) + '\n')
                    f.write('\n')   

        f.write('  total number of organizations                  : ' + str(metric_org_count) + '\n')
        f.write('  total number of sites                          : ' + str(metric_site_count) + '\n')
        f.write('  total number of registered subnets             : ' + str(metric_total_registered_subnets_count) + '\n')

    print('Site metrics appended to ' + os.getcwd() + '/' + metrics_output_file)
    print('Site details saved to ' + os.getcwd() + '/' + DATA_DIRECTORY)

if __name__ == '__main__':
    sites_healthcheck()