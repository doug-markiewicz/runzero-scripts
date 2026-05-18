load('json', json_encode='encode', json_decode='decode')
load('http', http_post='post', http_get='get', 'url_encode')

RUNZERO_BASE_URL = 'https://console.runzero.com/api/v1.0'
BULK_DELETE_BATCH_SIZE = 1000

# List of queries that will be run to delete assets from the runZero asset inventory. 
DELETE_ASSETS_QUERIES = [
    # Sample queries:
    #'source:shodan and source_count:=1',
    #'source:runzero and address_count:=1 and (primary_address:=fde0% or primary_address:=fe80%)'
]

# Fetch an API token using the provided client credentials.
def get_token(client_id, client_secret):
    url = '{}/account/api/token'.format(RUNZERO_BASE_URL)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    body = url_encode({
        'grant_type': 'client_credential',
        'client_id': client_id,
        'client_secret': client_secret,
    })

    response = http_post(url, headers=headers, body=bytes(body))
    if response.status_code != 200:
        print('Failed to fetch API token: {}'.format(response.status_code))
        return 

    response_json = json_decode(response.body)
    return response_json.get('access_token', None)

# Fetch a list of organizations accessible with the provided API token.
def get_orgs(token):
    url = '{}/account/orgs'.format(RUNZERO_BASE_URL)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(token)
    }
    response = http_get(url, headers=headers)
    if response.status_code != 200:
        print('Failed to fetch organizations: {}'.format(response.status_code))
        return 

    response_json = json_decode(response.body)
    if 'orgs' in response_json:
        return response_json['orgs']
    return response_json 

# Fetch asset IDs for a given organization and search query.
def get_asset_ids(token, org_name, org_id, search_query):
    #url = '{}/org/assets?_oid={}&search={}&fields={}'.format(RUNZERO_BASE_URL, org_id, search_query, 'id')
    url = '{}/org/assets'.format(RUNZERO_BASE_URL)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(token)
    }

    response = http_get(url, headers=headers, params={'_oid': org_id, 'search': search_query, 'fields': 'id'})
    if response.status_code != 200:
        print('Failed to fetch assets for org {} ({}) using query {} - {}'.format(org_name, org_id, search_query, response.status_code))
        return 

    response_json = json_decode(response.body)
    if 'assets' in response_json:
        assets = response_json['assets']
    else:
        assets = response_json

    asset_ids = []
    for asset in assets:
        asset_id = asset.get('id', '')
        if asset_id:
            asset_ids.append(asset_id)

    return asset_ids

# Delete assets in batches for a given organization and list of asset IDs.
def delete_assets(token, org_name, org_id, asset_ids):
    url = '{}/org/assets/bulk/delete?_oid={}'.format(RUNZERO_BASE_URL, org_id)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(token)
    }    
    total_assets = len(asset_ids)
    deleted_assets = 0

    for start in range(0, total_assets, BULK_DELETE_BATCH_SIZE):
        batch = asset_ids[start:start + BULK_DELETE_BATCH_SIZE]

        data = {
            'asset_ids': batch
        }

        response = http_post(url, headers=headers, body=bytes(json_encode(data)))
        if response.status_code != 204:
            print('Failed to delete assets for org {} ({}) - {}'.format(org_name, org_id, response.status_code))
            return False

        deleted_assets = deleted_assets + len(batch)
        print('Deleted {} of {} assets in org {} ({})'.format(deleted_assets, total_assets, org_name, org_id))

    return True

def main(*args, **kwargs):
    client_id = kwargs.get('access_key', '')
    client_secret = kwargs.get('access_secret', '')

    if not client_id or not client_secret:
        print('Missing required credentials: access_key and access_secret')
        return []

    token = get_token(client_id, client_secret)
    if not token:
        print('Failed to obtain API token with provided credentials.')
        return []

    orgs = get_orgs(token)
    if not orgs:
        print('No organizations were returned.')
        return []

    for org in orgs:
        org_id = org.get('id', '')
        org_name = org.get('name', org_id)
        print('Processing organization {} ({})'.format(org_name, org_id))

        for search_query in DELETE_ASSETS_QUERIES:
            asset_ids = get_asset_ids(token, org_name, org_id, search_query)
            
            if not asset_ids or len(asset_ids) == 0:
                print('0 assets found in {} ({}) using query {}'.format(org_name, org_id, search_query))
                continue

            print('Deleting {} assets in {} ({}) using query {}'.format(len(asset_ids), org_name, org_id, search_query))
            delete_assets(token, org_name, org_id, asset_ids)

    # This script performs maintenance only; return an empty import list.
    return []