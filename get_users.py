

from dotenv import load_dotenv
import os
import requests
import json
import csv
from collections import defaultdict
from datetime import datetime, date

load_dotenv()
RUNZERO_CLIENT_ID = os.getenv("RUNZERO_CLIENT_ID")
RUNZERO_CLIENT_SECRET = os.getenv("RUNZERO_CLIENT_SECRET")
RUNZERO_BASE_URL = 'https://console.runzero.com/api/v1.0'

# Authentication with client ID and secret and obtain bearer token
def get_token():
    url = f'{RUNZERO_BASE_URL}/account/api/token'
    header = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, data=data, headers=header, verify=True, auth=(RUNZERO_CLIENT_ID, RUNZERO_CLIENT_SECRET))
    if response.status_code != 200:
        print(f'Failed to obtain token from OAuth server: {response.status_code} {response.text}')
        exit(1)
    else:
        token_json = json.loads(response.text)
        return token_json['access_token']   

# Get all users within account
def get_users(token):
    url = f'{RUNZERO_BASE_URL}/account/users'
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f'Error fetching users: {response.status_code} {response.text}')
        exit(1)
    return response

# Map users to organizations based on effective_access object
def get_org_user_mapping(users_json):
    org_mapping = defaultdict(list)

    for user in users_json:
        name = user.get('name', '')
        email = user.get('email', '')
        access_list = user.get('effective_access', [])
        for access in access_list:
            org_id = access.get('organization_id', '')
            role_name = access.get('role_name', '')
            if org_id:
                org_mapping[org_id].append({
                    'name': name,
                    'email': email,
                    'role_name': role_name
                })
    return org_mapping

# Get organization name
def get_org_name(token, org_id):
    url = f'{RUNZERO_BASE_URL}/account/orgs/{org_id}'
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f'Error fetching organization name for org_id {org_id}: {response.status_code} {response.text}')
        return ''
    org_json = response.json()
    return org_json.get('name', '')

# Output final results to a csv file
def write_to_csv(output: list, filename: str, fieldnames: list):
    file = open(filename, 'w')
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output)
    file.close()

def main():
    access_token = get_token()

    # Get a list of all users and user attributes within the account

    users_output = []
    users_fields = [
        'id',
        'client_id',
        'created_at',
        'updated_at',
        'name',
        'first_name',
        'last_name',
        'email',
        'is_superuser',
        'password_enabled_at',
        'last_login_ip',
        'last_login_at',
        'last_login_ua',
        'last_activity_at',
        'sso_only',
        'login_failures',
        'actions',
        'last_action_at',
        'sso_group_mappings',
        'notification_email',
        'mfa_enabled',
        'groups',
        'org_default_role',
        'org_roles',
        'effective_access'
    ]

    users = get_users(access_token)
    users_json = users.json()

    for item in users_json:
        users_output.append({
                'id':item.get('id', ''),
                'client_id':item.get('client_id', ''),
                'created_at':item.get('created_at', ''),
                'updated_at':item.get('updated_at', ''),
                'name':item.get('name', ''),
                'first_name':item.get('first_name', ''),
                'last_name':item.get('last_name', ''),
                'email':item.get('email', ''),
                'is_superuser':item.get('client_admin', ''),
                'password_enabled_at':item.get('password_enabled_at', ''),
                'last_login_ip':item.get('last_login_ip', ''),
                'last_login_at':item.get('last_login_at', ''),
                'last_login_ua':item.get('last_login_ua', ''),
                'last_activity_at':item.get('last_activity_at', ''),
                'sso_only':item.get('sso_only', ''),
                'login_failures':item.get('login_failures', ''),
                'actions':item.get('actions', ''),
                'last_action_at':item.get('last_action_at', ''),
                'sso_group_mappings':item.get('sso_group_mappings', ''),
                'notification_email':item.get('notification_email', ''),
                'mfa_enabled':item.get('mfa_enabled', ''),
                'groups':item.get('groups', ''),
                'org_default_role':item.get('org_default_role', ''),
                'org_roles':item.get('org_roles', ''),
                'effective_access':item.get('effective_access', [])
        })

    write_to_csv(output=users_output, filename="get_users.csv", fieldnames=users_fields)

    # Create separate output file that maps users and their roles to each organizations; this is derived from the effective_access object.

    users_by_org_fields = [
        'organization_id',
        'organization_name', 
        'name', 
        'email', 
        'role_name'
    ]

    org_user_mapping = get_org_user_mapping(users_json)

    users_by_org_output = []
    for org_id, users in org_user_mapping.items():
        org_name = get_org_name(access_token, org_id)
        for user in users:
            users_by_org_output.append({
                'organization_id': org_id,
                'organization_name': org_name,
                'name': user.get('name', ''),
                'email': user.get('email', ''),
                'role_name': user.get('role_name', '')
            })
    
    write_to_csv(output=users_by_org_output, filename="get_users_by_org.csv", fieldnames=users_by_org_fields)
 
if __name__ == '__main__':
    main()