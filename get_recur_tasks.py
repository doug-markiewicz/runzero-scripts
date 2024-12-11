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
    recur_tasks_output = []
    recur_tasks_fields = [
        "organization_name",
        "organization_id",
        "task_id",
        "task_name",
        "description",
        "type",
        "status",
        "error",
        "created_by",
        "created_at",
        "updated_at",
        "site_id",
        "site_name",        
        "agent_id",
        "agent_name",           
        "start_time",
        "grace_period",
        "recur_frequency",
        "recur_last",
        "recur_next",
        "template_id",
        "scan_rate",
        "max_host_rate",
        "max_group_size",
        "host_ping",
        "subnet_ping",
        "subnet_ping_sample_rate",
        "nameservers",
        "targets",
        "excludes"        
    ]        

    access_token = get_token()
    orgs = get_organizations(access_token)

    for o in orgs:
        org_id = o.get('id', '')
        org_name = o.get('name', '')

        recur_tasks = get_recurring_tasks(access_token, org_id)
        recur_tasks_json = recur_tasks.json()      

        for item in recur_tasks_json:
            recur_tasks_output.append({
                'organization_name':org_name,
                'organization_id':org_id,
                'task_id':item.get('id', ''),
                'task_name':item.get('name', ''),
                'description':item.get('description', ''),        
                'type':item.get('type', ''),
                'status':item.get('status', ''),            
                'error':item.get('error', ''),
                'created_by':item.get('created_by', ''),
                'created_at':datetime.fromtimestamp(item.get('created_at', '')).strftime('%Y-%m-%d %H:%M:%S'), 
                'updated_at':datetime.fromtimestamp(item.get('updated_at', '')).strftime('%Y-%m-%d %H:%M:%S'), 
                'site_id':item.get('site_id', ''),
                'site_name':item.get('site_name', ''),                            
                'agent_id':item.get('agent_id', ''),
                'agent_name':item.get('agent_name', ''),
                'start_time':datetime.fromtimestamp(item.get('start_time', '')).strftime('%Y-%m-%d %H:%M:%S'), 
                'grace_period':item.get('grace_period', ''),
                'recur_frequency':item.get('recur_frequency', ''),
                'recur_last':datetime.fromtimestamp(item.get('recur_last', '')).strftime('%Y-%m-%d %H:%M:%S'),
                'recur_next':datetime.fromtimestamp(item.get('recur_next', '')).strftime('%Y-%m-%d %H:%M:%S'),
                'template_id':item.get('template_id', ''),
                'scan_rate':item.get('params', {}).get('rate', ''),
                'max_host_rate':item.get('params', {}).get('max-host-rate', ''), 
                'max_group_size':item.get('params', {}).get('max-group-size', ''),
                'host_ping':item.get('params', {}).get('host-ping', ''), 
                'subnet_ping':item.get('params', {}).get('subnet-ping', ''),   
                'subnet_ping_sample_rate':item.get('params', {}).get('subnet-ping-sample-rate', ''),
                'nameservers':item.get('params', {}).get('nameservers', ''),
                'targets':item.get('params', {}).get('targets', ''),
                'excludes':item.get('params', {}).get('excludes', ''),                                                                                                          
            })

    client_id = get_client_id(access_token)
    recur_tasks_output_file = 'tasks_recurring_' + client_id + '_' + date.today().strftime("%Y%m%d") + '.csv'
    write_to_csv(output=recur_tasks_output, filename=recur_tasks_output_file, fieldnames=recur_tasks_fields)
    print('Recurring tasks saved to ' + os.getcwd() + '/' + recur_tasks_output_file)

if __name__ == '__main__':
    main()