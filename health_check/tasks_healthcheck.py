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

def get_tasks(token, type=None):
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

# Output final results to a csv file
def write_to_csv(output: list, filename: str, fieldnames: list):
    file = open(filename, "w")
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output)
    file.close()

def tasks_healthcheck():

    access_token = get_token()

    metric_tasks_total = 0
    metric_tasks_analysis = 0
    metric_tasks_connector = 0
    metric_tasks_sample = 0
    metric_tasks_scan = 0
    metric_tasks_recurring = 0
    metric_tasks_recurring_active = 0
    metric_tasks_recurring_paused = 0
    metric_tasks_active = 0
    metric_tasks_canceled = 0
    metric_tasks_error = 0
    metric_tasks_new = 0
    metric_tasks_processed = 0
    metric_tasks_processing = 0
    metric_tasks_scanned = 0
    metric_tasks_stopped = 0
    metric_templates = 0
    metric_tasks_using_template = 0
    metric_recurring_tasks_analysis = 0
    metric_recurring_tasks_connector = 0
    metric_recurring_tasks_sample = 0
    metric_recurring_tasks_scan = 0
    metric_recurring_tasks_using_template = 0

    error_list = {}

    task_output = []
    task_fields = [
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
        "agent_id",
        "start_time",
        "targets",
        "template_name",
        "template_id",
        "rate",
        "runtime",
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
        "recv_bytes"
    ]    

    task_recur_output = []
    task_recur_fields = [
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

    access_token = get_token()
    client_id = get_client_id(access_token)    

    # Gather metrics on task templates
    templates = get_templates(access_token)
    templates_json = templates.json()

    for item in templates_json:
        metric_templates += 1

    # Gather metrics and produce output file for executed tasks
    tasks = get_tasks(access_token)
    tasks_json = tasks.json()   

    for item in tasks_json:

        metric_tasks_total += 1

        task_type = item.get('type', '')

        if task_type == 'analysis':
            metric_tasks_analysis += 1
        elif task_type == 'connector':
            metric_tasks_connector += 1
        elif task_type == 'sample':
            metric_tasks_sample += 1
        elif task_type == 'scan':
            metric_tasks_scan += 1
        else:
            print('Task type not recognized: ' + task_type)
            exit(1)        

        task_status = item.get('status', '')

        if task_status == 'active':
            metric_tasks_active += 1
        elif task_status == 'canceled':
            metric_tasks_canceled += 1
        elif task_status == 'error':
            metric_tasks_error += 1
        elif task_status == 'new':
            metric_tasks_new += 1
        elif task_status == 'processed':
            metric_tasks_processed += 1
        elif task_status == 'processing':
            metric_tasks_processing += 1
        elif task_status == 'scanned':
            metric_tasks_scanned += 1
        elif task_status == 'stopped':
            metric_tasks_stopped += 1
        else:
            print('Task status not recognized: ' + task_type)
            exit(1)

        if item.get('template_id') != '00000000-0000-0000-0000-000000000000':
            metric_tasks_using_template += 1

        task_error = item.get('error', '')
 
        if len(task_error) > 0:
            task_error = task_error.partition('\n')[0]
            if task_error in error_list:
                error_list[task_error] += 1
            else:
                error_list[task_error] = 1

        # Append explorer details to output file
        task_output.append({
            'organization_name':item.get('organization_name',''),
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
            'site_name':item.get('site_name',''),
            'site_id':item.get('site_id',''),
            'agent_name':item.get('agent_name',''),            
            'agent_id':item.get('agent_id',''),
            'start_time':item.get('start_time',''),
            'targets':item.get('targets',''),
            'template_name':item.get('template_name',''),
            'template_id':item.get('template_id',''),
            'rate':item.get('rate',''),                                                
            'runtime':item.get('site_id',''),
            'data_processing_started_at':datetime.fromtimestamp(item.get('data_processing_started_at', '')).strftime('%Y-%m-%d %H:%M:%S'),
            'data_processing_ended_at':datetime.fromtimestamp(item.get('data_processing_ended_at', '')).strftime('%Y-%m-%d %H:%M:%S'),                               
            'data_processing_duration':item.get('data_processing_duration',''),
            'data_acquisition_started_at':datetime.fromtimestamp(item.get('data_acquisition_started_at', '')).strftime('%Y-%m-%d %H:%M:%S'),
            'data_acquisition_started_at':datetime.fromtimestamp(item.get('data_acquisition_started_at', '')).strftime('%Y-%m-%d %H:%M:%S'),            
            'result_count':item.get('result_count',''),
            'sent_packets':item.get('sent',''),                                    
            'recv_packets':item.get('recv',''),
            'sent_bytes':item.get('sent_bytes',''),                                    
            'recv_bytes':item.get('recv_bytes','')  
        })

    # Gather metrics and produce output file for recurring tasks
    recur_tasks = get_tasks(access_token, 'recurring')
    recur_tasks_json = recur_tasks.json()
    
    for item in recur_tasks_json:
        
        metric_tasks_recurring += 1

        task_type = item.get('type', '')

        if task_type == 'analysis':
            metric_recurring_tasks_analysis += 1
        elif task_type == 'connector':
            metric_recurring_tasks_connector += 1
        elif task_type == 'sample':
            metric_recurring_tasks_sample += 1
        elif task_type == 'scan':
            metric_recurring_tasks_scan += 1
        else:
            print('Task type not recognized: ' + task_type)
            exit(1)        

        recur_task_status = item.get('status', '')

        if recur_task_status == 'active':
            metric_tasks_recurring_active += 1
        elif recur_task_status == 'paused':
            metric_tasks_recurring_paused += 1
        else:
            print('Recurring task status not recognized: ' + recur_task_status)
            exit(1)

        if item.get('template_id') != '00000000-0000-0000-0000-000000000000':
            metric_recurring_tasks_using_template += 1

        task_recur_output.append({
            'organization_name':item.get('organization_name', ''),
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

    DATA_DIRECTORY = 'data/' + date.today().strftime("%Y%m%d") + '_' + client_id

    # Check that the data directory exists
    if not os.path.isdir('data'):
        os.mkdir('data')

    # Check that the output folder exists
    if not os.path.isdir(DATA_DIRECTORY):
        os.mkdir(DATA_DIRECTORY)

    metrics_output_file = DATA_DIRECTORY + '/metrics.txt'
    task_output_file = DATA_DIRECTORY + '/tasks_output.csv'
    task_recur_output_file = DATA_DIRECTORY + '/tasks_recur_output.csv'

    # write tasks output file
    write_to_csv(output=task_recur_output, filename=task_recur_output_file, fieldnames=task_recur_fields)    
    write_to_csv(output=task_output, filename=task_output_file, fieldnames=task_fields)

    # write metrics
    with open(metrics_output_file, 'a') as f:
        f.write('task metrics (last 1000 tasks)                  \n')
        f.write('  analysis tasks                                ' + str(metric_tasks_analysis) + '\n')
        f.write('  connector tasks                               ' + str(metric_tasks_connector) + '\n')
        f.write('  sample tasks                                  ' + str(metric_tasks_sample) + '\n')
        f.write('  scan tasks                                    ' + str(metric_tasks_scan) + '\n')
        f.write('  scan tasks using a template                   ' + str(metric_tasks_using_template) + '\n')
        f.write('  task templates configured                     ' + str(metric_templates) + '\n')
        f.write('  active tasks                                  ' + str(metric_tasks_active) + '\n')
        f.write('  canceled tasks                                ' + str(metric_tasks_canceled) + '\n')
        f.write('  error tasks                                   ' + str(metric_tasks_error) + '\n')
        f.write('  new tasks                                     ' + str(metric_tasks_new) + '\n')
        f.write('  processed tasks                               ' + str(metric_tasks_processed) + '\n')
        f.write('  processing tasks                              ' + str(metric_tasks_processing) + '\n')
        f.write('  scanned tasks                                 ' + str(metric_tasks_scanned) + '\n')
        f.write('  stopped tasks                                 ' + str(metric_tasks_stopped) + '\n')
        f.write('\n')
        f.write('recurring task metrics:\n')
        f.write('  total recurring tasks                         ' + str(metric_tasks_recurring) + '\n')
        f.write('  active recurring tasks                        ' + str(metric_tasks_recurring_active) + '\n')
        f.write('  paused recurring tasks                        ' + str(metric_tasks_recurring_paused) + '\n')
        f.write('  recurring analysis tasks                      ' + str(metric_recurring_tasks_analysis) + '\n')
        f.write('  recurring connector tasks                     ' + str(metric_recurring_tasks_connector) + '\n')
        f.write('  recurring sample tasks                        ' + str(metric_recurring_tasks_sample) + '\n')
        f.write('  recurring scan tasks                          ' + str(metric_recurring_tasks_scan) + '\n')
        f.write('  recurring scan tasks using template           ' + str(metric_recurring_tasks_using_template) + '\n')        
        f.write('\n')
        f.write('task errors (last 1000 tasks):\n')
        for key, value in error_list.items():
            f.write('  ' + key + ' (' + str(value) + ')\n')
        f.write('\n')        

    print('Task metrics appended to ' + os.getcwd() + '/' + metrics_output_file)
    print('Task details saved to ' + os.getcwd() + '/' + task_output_file)
    print('Recurring task details saved to ' + os.getcwd() + '/' + task_recur_output_file)    

if __name__ == '__main__':
    tasks_healthcheck()