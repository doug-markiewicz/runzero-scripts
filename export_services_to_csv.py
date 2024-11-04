import requests
import os
import json
import csv
from dotenv import load_dotenv

load_dotenv()
RUNZERO_ORG_ID = os.getenv('RUNZERO_ORG_ID')
RUNZERO_EXPORT_TOKEN = os.getenv('RUNZERO_EXPORT_TOKEN')
RUNZERO_BASE_URL = 'https://console.runZero.com/api/v1.0'
CSV_FILE = '/Users/doug/Documents/Projects/runzero-scripts/export_services.csv'

# define runzero services query
# sample service query looks for tls certificates expiring in the next 30 days
QUERY = '_asset.protocol:tls and (tls.notAfterTS:>now and tls.notAfterTS:<30days)'

# define attributes that will be exported to csv
ATTRIBUTES = [
    'service_id',
    'service_address',
    'service_vhost',
    'service_transport',
    'service_port',
]

# optional list of service_data attributes to include in csv
# if empty, all service_data attributes will be exported
SERVICE_DATA_ATTRIBUTES = [
    'tls.cn',
    'tls.issuer',
    'tls.names',
    'tls.subject',
    'tls.notBefore',
    'tls.notAfter'
]

def main(): 
    # get services
    url = f'{RUNZERO_BASE_URL}/export/org/services.json?_oid={RUNZERO_ORG_ID}&search={QUERY}'
    header = {"Content-Type": "application/json", "Authorization": "Bearer " + RUNZERO_EXPORT_TOKEN}
    services = requests.get(url, headers=header)
    services_json = services.json()

    output = []
    for s in services_json:
        row = {}
        for a in ATTRIBUTES:
            row[a] = s.get(a, '')

        service_data = s.get('service_data', {})
        if service_data:
            if SERVICE_DATA_ATTRIBUTES:
                for attrib in SERVICE_DATA_ATTRIBUTES:
                    row[attrib] = service_data.get(attrib, '')
            else:
                for attrib in service_data:
                    row[attrib] = service_data.get(attrib, '')

        output.append(row)

    # export .csv file and create assets in runZero
    with open(CSV_FILE, mode='w') as file:
        writer = csv.DictWriter(file, fieldnames=output[0].keys())
        writer.writeheader()
        writer.writerows(output)

if __name__ == '__main__':
    main()