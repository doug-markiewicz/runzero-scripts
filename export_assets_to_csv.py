import requests
import os
import json
import csv
from datetime import datetime

# these can be removed if you are hard coding the org id and export token
from dotenv import load_dotenv
load_dotenv()

# load global variables from .env file
# alternatively you can hard code the org id and export token
RUNZERO_ORG_ID = os.getenv('RUNZERO_ORG_ID')
RUNZERO_EXPORT_TOKEN = os.getenv('RUNZERO_EXPORT_TOKEN')
RUNZERO_BASE_URL = 'https://console.runZero.com/api/v1.0'

# set the path of export files
CSV_FILE = '/Users/doug/Documents/Projects/runzero-scripts/export_assets.csv'

# define runzero asset query; this should match a valid query within the platform
# sample asset query looks looks for all desktops and laptops seen within the last 30 days
QUERY = 'last_seen:<30days and (type:desktop or type:laptop or name:desktop or name:laptop)'

# define attributes that will be exported to csv
# attributes must match keys in an assets json export
# if an attribute is presented as an array, it should be added to an if statement below that parses arrays
ASSET_ATTRIBUTES = [
    'id',
    'addresses',
    'macs',
    'mac_vendors',
    'names',
    'type',
    'tags',
    'os_vendor',
    'os_product',
    'os_version',
    'hw_vendor',
    'hw_product',
    'hw_version',
    '@crowdstrike.dev.hostname',
    '@crowdstrike.dev.siteName',
    '@crowdstrike.dev.lastLoginTS',
    '@crowdstrike.dev.lastLoginUser',
    '@crowdstrike.dev.lastSeen',
    '@crowdstrike.dev.lastReboot',    
    '@crowdstrike.dev.systemManufacturer',
    '@crowdstrike.dev.systemProductName',
    '@crowdstrike.dev.biosManufacturer',
    '@crowdstrike.dev.biosVersion',
    '@crowdstrike.dev.discover.cpuProcessorName',
    '@crowdstrike.dev.discover.systemSerialNumber',
    '@crowdstrike.dev.discover.city',
    '@crowdstrike.dev.discover.country',
    '@intune.dev.deviceName',
    '@intune.dev.serialNumber',
    '@intune.dev.manufacturer',
    '@intune.dev.model',
    '@intune.dev.userDisplayName',
    '@intune.dev.userID',
    '@intune.dev.userPrincipalName',
]

def main():

    # export asset records based on defined query
    print(datetime.now().strftime('%Y%m%d %H:%M:%S ') + 'exporting assets from /export/org/assets.json (this may take a few minutes)')
    url = f'{RUNZERO_BASE_URL}/export/org/assets.json?_oid={RUNZERO_ORG_ID}&search={QUERY}'
    header = {"Content-Type": "application/json", "Authorization": "Bearer " + RUNZERO_EXPORT_TOKEN}
    assets = requests.get(url, headers=header)
    if assets.status_code != 200:
        print('Failed to export assets from ' + url)
        exit(1)    
    assets_json = assets.json()

    # parse relevant attributes from asset records
    print(datetime.now().strftime('%Y%m%d %H:%M:%S ') + 'parsing defined attributes')
    output = []
    for asset in assets_json:
        record = {}
        for a in ASSET_ATTRIBUTES: 
            
            # handle attributes that are presented as an array        
            if a == 'names' or a == 'addresses' or a == 'macs' or a == 'mac_vendors' or a == 'tags':
                attrib = json.dumps(asset.get(a,''))
                attrib = attrib.replace('[','').replace(']','').replace('{','').replace('}','').replace('"','')
                record[a] = attrib
            
            # handle foreign asset attributes
            elif a.startswith('@'):  
                split_a = a.split('.',2)
                foreign_attribute_source = split_a[0] + '.' + split_a[1]
                foreign_attribute = split_a[2]
                foreign_asset_records = []
                foreign_asset_records = asset.get('foreign_attributes', {}).get(foreign_attribute_source, [])

                # check for one or more of the same foreign asset attribute and take the newest
                if foreign_asset_records:
                    if len(foreign_asset_records) > 1:
                        most_recent_foreign_asset = foreign_asset_records[0]
                        for f in foreign_asset_records:
                            timestamp = int(f.get('ts', '0'))
                            most_recent_timestamp = int(most_recent_foreign_asset.get('ts', '0'))
                            if timestamp > most_recent_timestamp:
                                most_recent_foreign_asset = f
                            record[a] = most_recent_foreign_asset.get(foreign_attribute, '')
                    else:
                        record[a] = foreign_asset_records[0].get(foreign_attribute, '')
            else:    
                record[a] = asset.get(a, '')

        output.append(record)

    # export assets to csv file
    with open(CSV_FILE, mode='w') as file:
        writer = csv.DictWriter(file, fieldnames=ASSET_ATTRIBUTES)
        writer.writeheader()
        writer.writerows(output)
        print(datetime.now().strftime('%Y%m%d %H:%M:%S ') + 'assets saved to ' + CSV_FILE)

if __name__ == '__main__':
    main()