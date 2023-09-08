import requests
import json
import csv 
from flatten_json import flatten
from datetime import datetime
from typing import Any, Dict, List

'''
    The following attributes need to be configured to match the account that is being queried. If you are a SaaS customer, the base url and token url
    should remain the same. If you have an on-premise deployment, then console.runzero.com will need to be updated with the console address. This 
    script uses the account API in order to query across organizations. Visiting the following URL for instructions on creating account API credentials.

    https://www.runzero.com/docs/leveraging-the-api/#account-api
'''
RUNZERO_BASE_URL = 'https://console.runzero.com/api/v1.0'
RUNZERO_TOKEN_URL = 'https://console.runzero.com/api/v1.0/account/api/token'
RUNZERO_CLIENT_ID = ''
RUNZERO_CLIENT_SECRET = 'ls -l'

'''
    The output csv file will be limited to the following list of attributes. This list can be adjusted to reflect the attributes that you need. The 
    following link illustrates all available attributes from an explorer json.

    https://github.com/doug-markiewicz/runzero-scripts/blob/main/get_explorers_sample_explorer_json.json
'''
EXPLORER_FIELD_INCLUDE_LIST = [
    "id", 
    "organization_id",
    "name", 
    "last_checkin", 
    "os",
    "version",
    "path",
    "pid",
    "settings"
    "external_ip",
    "internal_ip",
    "connected",
    "inactive"
]

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
    exp = requests.get(f'{RUNZERO_BASE_URL}/org/explorers?_oid={org_id}', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if exp.status_code != 200:
        print("Failed to retrieve explorer data.")
        exit(1)
    return json.loads(exp.text)

# Output final results to a csv file
def write_to_csv(output: dict, filename: str, fieldnames: list):
    file = open(filename, "w")
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output)
    file.close()

def main():
    access_token = get_token()
    orgs = get_organizations(access_token)
    
    explorer_output = []
    columns = []
    columns.append("organization_name")
    for o in orgs:
        org_id = o.get('id', '')
        org_name = o.get('name', '')
        explorers = get_explorers(access_token, org_id)
        if len(explorers) > 0:
            for e in explorers:
                row = {}
                row["organization_name"] = org_name
                for attribute in e.keys():
                    if attribute in EXPLORER_FIELD_INCLUDE_LIST:
                        if attribute == 'last_checkin':
                            e[attribute] = datetime.fromtimestamp(e[attribute]).strftime('%Y-%m-%d %H:%M:%S') # Converts epoch to readable date time format
                        row[attribute] = e[attribute]
                        if attribute not in columns:
                            columns.append(attribute)
                explorer_output.append(row)

    write_to_csv(output=explorer_output, filename="get_explorers_output.csv", fieldnames=columns)

if __name__ == '__main__':
    main()