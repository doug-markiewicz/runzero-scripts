load('runzero.types', 'ImportAsset', 'NetworkInterface')
load('json', json_encode='encode', json_decode='decode')
load('net', 'ip_address')
load('http', http_post='post', http_get='get', 'url_encode')
load('uuid', 'new_uuid')

DIGITAL_OCEAN_OAUTH_URL = 'https://cloud.digitalocean.com/v1/'
DIGITAL_OCEAN_API_URL = 'https://api.digitalocean.com/v2/'
RUNZERO_REDIRECT = 'https://console.runzero.com/'

# kwargs = {"access_key":"de6432a7dd86de573b506c2d198d601aa1b3e1c6ff47bae2a98a855d2ae6c524", "access_secret":"963c6879ec49ef251b081d5a6a6c338b01c66b8a31a7f8d55247e93499efb133"}

def get_auth_token(access_key):
    random = new_uuid
    url = '{}/{}?response_type={}&client_id={}&redirect={}&scope={}&state={}'.format(DIGITAL_OCEAN_OAUTH_URL, 'oauth/token', 'code', access_key, RUNZERO_REDIRECT, 'read', random)
    auth_token = http_get(url, headers={"Content-Type": "application/json"})
    if auth_token.status_code != 200:
        print('failed to retrieve authorization token')
        return None
    print(auth_token)
    print(auth_token.body)
    return

def get_access_token(access_key, access_secret):
    #url = '{}/{}?grant_type={}&code={}&client_id={}&client_secret={}&redirect_uri={}'.format(DIGITAL_OCEAN_OAUTH_URL, 'oauth/token', auth_token, access_key, access_secret, RUNZERO_REDIRECT)
    url = '{}/{}?client_id={}&client_secret={}'.format(DIGITAL_OCEAN_OAUTH_URL, 'oauth/token', access_key, access_secret)
    token = http_post(url, headers={"Content-Type": "application/json"})
    if token.status_code != 200:
        print('failed to retrieve access token')
        return None
    #token_json = json_decode(token.body)
    print(token.body)
    return token.body

def build_assets(assets_json):
    assets_import = []
    for item in assets_json:
        id = item.get('id', new_uuid)        
        hostname = item.get('name', '')

        ips = []
        '''
        int_ip = item.get('int_ip', '')
        if int_ip:
            ips.append(int_ip)
        ext_ip = item.get('ext_ip', '')
        if ext_ip:
            ips.append(ext_ip)
        '''
        device = []
        macs = []
        device = item.get('device', {})
        if device:
            macs = device.get('macAddress', [])

        if macs:
            for m in macs:
                network = build_network_interface(ips=ips, mac=m)
        else:
            network = build_network_interface(ips=ips, mac=None)

        # handle additional attributes collected for asset
        custom_attrs = {}
        custom_attribs_to_ignore = [
            "id",
            "name",
        ]

        #flattened_item = flatten_json(item)

        for key, value in item.items():
            if type(value) != 'dict':
                if key not in custom_attribs_to_ignore:
                    custom_attrs[key] = str(value)[:1023]

        assets_import.append(
            ImportAsset(
                id=str(id),
                hostnames=[hostname],
                networkInterfaces=[network],
                customAttributes=custom_attrs
            )
        )
    return assets_import

# Build runZero network interfaces; shouldn't need to touch this
def build_network_interface(ips, mac):
    ip4s = []
    ip6s = []
    for ip in ips[:99]:
        ip_addr = ip_address(ip)
        if ip_addr.version == 4:
            ip4s.append(ip_addr)
        elif ip_addr.version == 6:
            ip6s.append(ip_addr)
        else:
            continue
    if not mac:
        return NetworkInterface(ipv4Addresses=ip4s, ipv6Addresses=ip6s)
    
    return NetworkInterface(macAddress=mac, ipv4Addresses=ip4s, ipv6Addresses=ip6s)

def main(**kwargs):
    access_key = kwargs['access_key']
    access_secret = kwargs['access_secret']

    #auth_token = get_auth_token(access_key)

    access_token = get_access_token(access_key, access_secret)

    '''
    # Get assets
    assets = []
    url = '{}/{}/'.format(DIGITAL_OCEAN_API_URL, 'public/assets')
    assets = http_get(url, headers={"Content-Type": "application/json", "Authorization": "Bearer " + access_token})
    if assets.status_code != 200:
        print('failed to retrieve assets')
        return None

    assets_json = json_decode(assets.body)['data']
    print(assets_json)

    assets_import = build_assets(assets_json)
    if not assets_import:
        print('no assets')
    
    return assets_import
    '''
