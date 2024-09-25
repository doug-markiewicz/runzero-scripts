from dotenv import load_dotenv
import os
import requests
import json
import csv

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

# Get all sites for the specified organization
def get_sites(token, org_id):
    sites = requests.get(f'{RUNZERO_BASE_URL}/org/sites?_oid={org_id}', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if sites.status_code != 200:
        print("Failed to retrieve site data for org {org_id}.")
        exit(1)
    return json.loads(sites.text)

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
    
    subnets_output = []
    subnets_fields = [
        'organization_id',
        'organization_name',
        'site_id',
        'site_name',
        'registered_subnet',
        'description',
        'tags'
    ]

    for o in orgs:
        org_id = o.get('id', '')
        org_name = o.get('name', '')
        
        sites = get_sites(access_token, org_id)

        for s in sites:
            site_id = s.get('id', '')
            site_name = s.get('name', '')
            subnets = s.get('subnets', '')
            for key, value in subnets.items():
                subnets_output.append({
                    'organization_id':org_id,
                    'organization_name':org_name,
                    'site_id':site_id,
                    'site_name':site_name,
                    'registered_subnet':key,
                    'description':value.get('description', ''),
                    'tags':value.get('tags','')
                })
    
    write_to_csv(output=subnets_output, filename="get_registered_subnets_output.csv", fieldnames=subnets_fields)

if __name__ == '__main__':
    main()