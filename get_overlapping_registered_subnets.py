from dotenv import load_dotenv
import os
import requests
import ipaddress
from itertools import combinations

load_dotenv()
RUNZERO_BASE_URL = 'https://console.runzero.com/api/v1.0'
RUNZERO_ORG_TOKEN = os.getenv('RUNZERO_ORG_TOKEN')
RUNZERO_ORG_ID = os.getenv('RUNZERO_ORG_ID')

SITES_TO_IGNORE = [
    'Excluded Site 1',
    'Excluded Site 2',
    'Excluded Site 3'
]

SUBNETS_TO_IGNORE = [
    ipaddress.ip_network('192.168.1.0/24')
]

# Get all sites within specified organization
def get_sites(token, org_id):
    sites = requests.get(f'{RUNZERO_BASE_URL}/org/sites?_oid={org_id}', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if sites.status_code != 200:
        print('Failed to retrieve site data. ', sites.status_code)
        exit(1)
    return sites.json()

# Parse registered subnets
def parse_subnets(site):
    subnets = site.get('subnets', {})
    out = []
    for key in subnets.keys():
        net = ipaddress.ip_network(key)
        if net not in SUBNETS_TO_IGNORE:
            out.append((net, site['id'], site['name']))
    return out

# Find overlaps in registered subnets
def find_overlaps(subnet_list):
    overlaps = []
    for (net1, sid1, name1), (net2, sid2, name2) in combinations(subnet_list, 2):
        if sid1 != sid2 and net1.overlaps(net2):
            overlaps.append({'site1_id': sid1, 'site1_name': name1, 'subnet1': str(net1), 'site2_id': sid2, 'site2_name': name2, 'subnet2': str(net2)})
    return overlaps

def main():
    sites = get_sites(RUNZERO_ORG_TOKEN, RUNZERO_ORG_ID)
    subnets = []
    for site in sites:
        site_name = site.get('name')
        if site_name not in SITES_TO_IGNORE:
            subnets += parse_subnets(site)

    overlaps = find_overlaps(subnets)

    if not overlaps:
        print('No overlapping registered subnets found in this organization.')
    else:
        print('Overlapping subnets found:')
        for o in overlaps:
            print(f'Site {o["site1_name"]} ({o["site1_id"]}) subnet {o["subnet1"]} overlaps with site {o["site2_name"]} ({o["site2_id"]}) subnet {o["subnet2"]}')

if __name__ == '__main__':
    main()
