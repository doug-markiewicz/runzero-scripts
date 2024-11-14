# sync_perimeter_scans.py
#
# This script is intended for self-hosted customers that want to leverage hosted explorers for perimeter scans. It will pull perimeter scans 
# from the configured SaaS instance and import them into the configured self-hosted instance. Scan data files are temporarily stored on the
# local file system in the same path as the script. This script will also create a log file in the same path as the script.
#
# Instructions:
#     1) Set SaaS environment parameters
#     2) Set self hosted environment parameters
#     3) Set clean-up parameters
#     4) run python3 sync_perimeter_scans.py

from dotenv import load_dotenv
import requests
import logging
import os

load_dotenv()

SELF_ORG_ID = '3a1edcc5-12f9-4ff2-a2e8-99364157e5ac'
SELF_SITE_ID = '00e12372-c88a-4154-9532-6333d420460c'
SELF_BASE_URL = '192.168.2.200'
SELF_ORG_TOKEN = os.getenv('SELF_ORG_TOKEN')

SAAS_ORG_ID = '98828456-f9ee-485d-aff6-11ddc91b2468'
SAAS_SITE_ID = 'd3cb8226-f531-41a6-a334-a0bb7e981460'
SAAS_BASE_URL = 'console.runzero.com'
SAAS_ORG_TOKEN = os.getenv('SAAS_ORG_TOKEN')
SAAS_TASK_SEARCH_FILTER = 'name:="Perimeter Scan - Daily" and status:"Processed" and updated_at:<24hours'

'''
The folowing parameters determine clean-up behavior following the sync. 
   HIDE_TASKS_ON_SYNC - Hide tasks within the SaaS console. Data/logs associated with the task will no longer be accessible from the SaaS console. 
   DELETE_LOCAL_FILES - Clean-up gzip files stored on your local filesystem as part of running this script.
'''
HIDE_TASKS_ON_SYNC = False
DELETE_LOCAL_FILES = True

def get_tasks():
    url = f'https://{SAAS_BASE_URL}/api/v1.0/org/tasks?search={SAAS_TASK_SEARCH_FILTER}&_oid={SAAS_ORG_ID}'
    response = requests.get(url, headers={"Content-Type": "application/json", "Authorization": "Bearer " + SAAS_ORG_TOKEN})

    if response.status_code == 200:
        logging.info(f'Successfully downloaded completed scan tasks from {SAAS_BASE_URL}')
    else:
        logging.error(f'Failed to download scan tasks. Status code: {response.status_code}, Response: {response.text}')   

    return response

def get_task_data(task_id):
    url = f'https://{SAAS_BASE_URL}/api/v1.0/org/tasks/{task_id}/data'
    with open(f'scan_{task_id}.json.gz', 'wb') as f:
        response = requests.get(url, headers={"Content-Type": "application/octet-stream", "Authorization": "Bearer " + SAAS_ORG_TOKEN}, stream=True)

        if response.status_code == 200:
            logging.info(f'Successfully downloaded task {task_id} from {SAAS_BASE_URL}')
        else:
            logging.error(f'Failed to download task {task_id} from {SAAS_BASE_URL}. Status code: {response.status_code}, Response: {response.text}')   

        for chunk in response.raw.stream(1024, decode_content=False):
            if chunk:
                f.write(chunk)
    
        return response

def upload_task_data(task_id, task_data):
    url = f'https://{SELF_BASE_URL}/api/v1.0/org/sites/{SELF_SITE_ID}/import?_oid={SELF_ORG_ID}'
    with open(f'scan_{task_id}.json.gz', 'rb') as file:
        response = requests.put(url, headers={"Content-Type": "application/octet-stream", "Authorization": "Bearer " + SELF_ORG_TOKEN}, verify=False, stream=True, data=file)
        
        if response.status_code == 200:
            logging.info(f'Successfully uploaded task {task_id} to {SELF_BASE_URL}')
        else:
            logging.error(f'Failed to upload task {task_id} to {SELF_BASE_URL}. Status code: {response.status_code}, Response: {response.text}')        

        return response
    
def hide_task(task_id):
    url = f'https://{SAAS_BASE_URL}/api/v1.0/org/tasks/{task_id}/hide?_oid={SAAS_ORG_ID}'
    response = requests.post(url, headers={"Content-Type": "application/json", "Authorization": "Bearer " + SAAS_ORG_TOKEN})   

    if response.status_code == 200:
        logging.info(f'Task {task_id} was successfully hidden on {SAAS_BASE_URL}')
    else:
        logging.error(f'Failed to hide task {task_id} on {SAAS_BASE_URL}. Status code: {response.status_code}, Response: {response.text}')
    
    return response

def main():

    # Set logging paramters
    logging.basicConfig(filename='sync_perimeter_scans.log', format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', encoding='utf-8', level=logging.DEBUG)

    # Get all tasks
    tasks = get_tasks()
    tasks_json = tasks.json()

    if len(tasks_json) == 0:
        logging.info(f'No tasks found on {SAAS_BASE_URL} using the search filter ({SAAS_TASK_SEARCH_FILTER}).')
        exit(0)

    for t in tasks_json:
        # Parse task ID
        task_id = t.get('id', '')

        # Download task data from SaaS instance for each task
        task_data = get_task_data(task_id)

        # Upload task data to self hosted console
        upload_task_data(task_id, task_data)

        logging.info(f'Task ID {task_id} successfully synced to {SELF_BASE_URL} from {SAAS_BASE_URL}')

        # Hide task on SaaS instance once sync occurs with self hosted instance
        if HIDE_TASKS_ON_SYNC:
            hide_task(task_id)
        
        # Clean up tasks data stored on local file system during sync process
        if DELETE_LOCAL_FILES:
            try:
                os.remove(f'scan_{task_id}.json.gz')
                logging.info(f'scan_{task_id}.json.gz was successfully removed from local file system')
            except ValueError:
                logging.info(f'Failed to remove scan_{task_id}.json.gz from local filesystem')

if __name__ == '__main__':
    main()
