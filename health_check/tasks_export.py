from dotenv import load_dotenv
import os
import requests
import json
import csv
import textwrap
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

# Get templates
def get_templates(token):
    templates = requests.get(f'{RUNZERO_BASE_URL}/account/tasks/templates', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if templates.status_code != 200:
        print("Failed to retrieve task templates.")
        exit(1)
    return templates

# Get client id
def get_client_id(token):
    account = requests.get(f'{RUNZERO_BASE_URL}/account/orgs', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if account.status_code != 200:
        print("Failed to retrieve account information.")
        exit(1)
    account_json = account.json()
    return account_json[0].get('client_id','')

def get_task_output(token, task_type, recurring):
    search = quote('type:=' + task_type + ' and recur:=' + recurring)    
    tasks = requests.get(f'{RUNZERO_BASE_URL}/account/tasks?search={search}', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if tasks.status_code != 200:
        print("Failed to retrieve task data.")
        exit(1)
    tasks_json = tasks.json()
    
    task_output = []
    for item in tasks_json:
        data_acquisition_started_at = item.get('data_acquisition_started_at', '')
        data_acquisition_ended_at = item.get('data_acquisition_ended_at', '')
        data_acquisition_duration = data_acquisition_ended_at - data_acquisition_started_at
        data_processing_started_at = item.get('data_processing_started_at', '')
        data_processing_ended_at = item.get('data_processing_ended_at', '')
        data_processing_duration = data_processing_ended_at - data_processing_started_at

        task_output.append({
            'organization_id':item.get('organization_id',''),
            'id':item.get('id',''),
            'name':item.get('name'),
            'description':item.get('description'),            
            'type':item.get('type',''),
            'status':item.get('status',''),            
            'error':item.get('error',''),
            'created_by':item.get('created_by',''),
            'created_at':datetime.fromtimestamp(item.get('created_at', '')).strftime('%Y-%m-%d %H:%M:%S'), 
            'updated_at':datetime.fromtimestamp(item.get('updated_at', '')).strftime('%Y-%m-%d %H:%M:%S'), 
            'site_id':item.get('site_id',''),     
            'agent_id':item.get('agent_id',''),
            'start_time':datetime.fromtimestamp(item.get('start_time', '')).strftime('%Y-%m-%d %H:%M:%S'), 
            'grace_period':item.get('grace_period', ''),
            'recur_frequency':item.get('recur_frequency',''),
            'recur_last':datetime.fromtimestamp(item.get('recur_last', '')).strftime('%Y-%m-%d %H:%M:%S'),
            'recur_next':datetime.fromtimestamp(item.get('recur_next', '')).strftime('%Y-%m-%d %H:%M:%S'),
            'targets':item.get('params', {}).get('targets',''),
            'excludes':item.get('params', {}).get('excludes',''), 
            'template_id':item.get('template_id',''),
            'scan_rate':item.get('params', {}).get('rate',''),
            'max_host_rate':item.get('params', {}).get('max-host-rate',''), 
            'max_group_size':item.get('params', {}).get('max-group-size',''), 
            'host_ping':item.get('params', {}).get('host-ping', ''),
            'subnet_ping':item.get('params', {}).get('subnet-ping',''),   
            'subnet_ping_sample_rate':item.get('params', {}).get('subnet-ping-sample-rate',''),
            'nameservers':item.get('params', {}).get('nameservers', ''),                                                                                         
            'data_processing_started_at':datetime.fromtimestamp(data_processing_started_at).strftime('%Y-%m-%d %H:%M:%S'),
            'data_processing_ended_at':datetime.fromtimestamp(data_processing_ended_at).strftime('%Y-%m-%d %H:%M:%S'),                               
            'data_processing_duration':data_processing_duration,
            'data_acquisition_started_at':datetime.fromtimestamp(data_acquisition_started_at).strftime('%Y-%m-%d %H:%M:%S'),
            'data_acquisition_ended_at':datetime.fromtimestamp(data_acquisition_ended_at).strftime('%Y-%m-%d %H:%M:%S'),  
            'data_acquisition_duration':data_acquisition_duration,
            'result_count':item.get('stats', {}).get('ResultCount',''),
            'sent_packets':item.get('stats', {}).get('Sent',''),                                    
            'recv_packets':item.get('stats', {}).get('Recv',''),
            'sent_bytes':item.get('stats', {}).get('SentBytes',''),                                    
            'recv_bytes':item.get('stats', {}).get('RecvBytes',''),
            'size_site':item.get('size_site', ''),
            'size_data':item.get('size_data', ''),
            'size_results':item.get('size_results', ''),
            'assets_new':item.get('stats', {}).get('change.newAssets',''),
            'assets_back_online':item.get('stats', {}).get('change.onlineAssets',''),
            'assets_marked_offline':item.get('stats', {}).get('change.offlineAssets',''),
            'assets_changed':item.get('stats', {}).get('change.changedAssets',''),
            'assets_unchanged':item.get('stats', {}).get('change.unchangedAssets',''),
            'assets_ignored':item.get('stats', {}).get('change.ignoredAssets',''),
            'users_new':item.get('stats', {}).get('change.newDirectoryUsers',''),
            'users_changed':item.get('stats', {}).get('change.changedDirectoryUsers',''),
            'users_unchanged':item.get('stats', {}).get('change.unchangedDirectoryUsers','0'),
            'users_total':item.get('stats', {}).get('change.totalDirectoryUsers','0'),
            'groups_new':item.get('stats', {}).get('change.newDirectoryGroups',''),
            'groups_changed':item.get('stats', {}).get('change.changedDirectoryGroups',''),
            'groups_unchanged':item.get('stats', {}).get('change.unchangedDirectoryGroups',''),
            'groups_total':item.get('stats', {}).get('change.totalDirectoryGroups','')
        })

    return task_output

# Output final results to a csv file
def write_to_csv(output: list, filename: str, fieldnames: list):
    file = open(filename, "w")
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output)
    file.close()

def main():
    access_token = get_token()

    task_fields = [
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
        "site_id",
        "agent_id",
        "start_time",
        "grace_period",
        "recur_frequency",
        "recur_last",
        "recur_next",
        "targets",
        "excludes",        
        "template_id",
        "scan_rate",
        "max_host_rate",
        "max_group_size",
        "host_ping",
        "subnet_ping",
        "subnet_ping_sample_rate",
        "nameservers",
        "data_processing_started_at",
        "data_processing_ended_at",
        "data_processing_duration",
        "data_acquisition_started_at",
        "data_acquisition_ended_at",
        "data_acquisition_duration",
        "result_count",
        "sent_packets",
        "recv_packets",
        "sent_bytes",
        "recv_bytes",
        "size_site",
        "size_data",
        "size_results",
        "assets_new",
        "assets_back_online",
        "assets_marked_offline",
        "assets_changed",
        "assets_unchanged",
        "assets_ignored",
        "users_new",
        "users_changed",
        "users_unchanged",
        "users_total",
        "groups_new",
        "groups_changed",
        "groups_unchanged",
        "groups_total"
    ]    

    access_token = get_token()
    client_id = get_client_id(access_token)    

    # Gather metrics and produce output file for processed scan tasks
    scan_task_output = []
    task_type = 'scan'
    recurring = 'false'
    scan_task_output = get_task_output(access_token, task_type, recurring)
    scan_task_output_file = 'tasks_scan_' + client_id + '_' + date.today().strftime("%Y%m%d") + '.csv'
    write_to_csv(output=scan_task_output, filename=scan_task_output_file, fieldnames=task_fields)
    print('Scan tasks saved to ' + os.getcwd() + '/' + scan_task_output_file)

    # Gather metrics and produce output file for processed connector tasks
    connector_task_output = []
    task_type = 'connector'
    recurring = 'false'
    connector_task_output = get_task_output(access_token, task_type, recurring)
    connector_task_output_file = 'tasks_connector_' + client_id + '_' + date.today().strftime("%Y%m%d") + '.csv'
    write_to_csv(output=connector_task_output, filename=connector_task_output_file, fieldnames=task_fields)
    print('Connector tasks saved to ' + os.getcwd() + '/' + connector_task_output_file)

    # Gather metrics and produce output file for recurring tasks
    recur_task_output = []
    task_type = '%'
    recurring = 'true'
    recur_task_output = get_task_output(access_token, task_type, recurring)
    recur_task_output_file = 'tasks_recurring_' + client_id + '_' + date.today().strftime("%Y%m%d") + '.csv'
    write_to_csv(output=recur_task_output, filename=recur_task_output_file, fieldnames=task_fields)
    print('Recurring tasks saved to ' + os.getcwd() + '/' + recur_task_output_file)

if __name__ == '__main__':
    main()