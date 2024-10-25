from dotenv import load_dotenv
import os
import requests
import json
import csv
from datetime import datetime, date
from urllib.parse import quote

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

# Get all tasks within specified organization
def get_recurring_tasks(token, org_id):
    search = quote('recur:=true')
    tasks = requests.get(f'{RUNZERO_BASE_URL}/org/tasks?search={search}&_oid={org_id}', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if tasks.status_code != 200:
        print("Failed to retrieve task data.")
        exit(1)
    return tasks

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

    recur_tasks_output = []
    recur_tasks_fields = [
        "organization_name",
        "organization_id",
        "id",
        "name",
        "description",
        "type",
        "status",
        "error",
        "created_by",
        "created_at",
        "updated_at",        
        "site_name",
        "site_id",
        "agent_name",
        "agent_id",
        "frequency",
        "recur_last",
        "recur_next",
        "targets",
        "template_name",
        "template_id",
        "rate"
    ]    

    for o in orgs:
        org_id = o.get('id', '')
        org_name = o.get('name', '')

        recur_tasks = get_recurring_tasks(access_token, org_id)
        recur_tasks_json = recur_tasks.json()      

        for item in recur_tasks_json:
            recur_tasks_output.append({
                'organization_name':org_name,
                'organization_id':org_id,
                'id':item.get('id',''),
                'name':item.get('name'),
                'description':item.get('description'),            
                'type':item.get('type',''),
                'status':item.get('status',''),            
                'error':item.get('error',''),
                'created_by':item.get('created_by',''),
                'created_at':datetime.fromtimestamp(item.get('created_at', '')).strftime('%Y-%m-%d %H:%M:%S'), 
                'updated_at':datetime.fromtimestamp(item.get('updated_at', '')).strftime('%Y-%m-%d %H:%M:%S'), 
                'site_name':item.get('site_name',''),
                'site_id':item.get('site_id',''),
                'agent_name':item.get('agent_name',''),            
                'agent_id':item.get('agent_id',''),
                'frequency':item.get('agent_id',''),
                'recur_last':datetime.fromtimestamp(item.get('recur_last', '')).strftime('%Y-%m-%d %H:%M:%S'), 
                'recur_next':datetime.fromtimestamp(item.get('recur_next', '')).strftime('%Y-%m-%d %H:%M:%S'), 
                'targets':item.get('targets',''),
                'template_name':item.get('template_name',''),
                'template_id':item.get('template_id',''),
                'rate':item.get('rate','')       
            })

    write_to_csv(output=recur_tasks_output, filename="get_recur_tasks_output.csv", fieldnames=recur_tasks_fields)

if __name__ == '__main__':
    main()