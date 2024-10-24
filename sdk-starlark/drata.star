load('runzero.types', 'ImportAsset', 'NetworkInterface')
load('json', json_encode='encode', json_decode='decode')
load('net', 'ip_address')
load('http', http_post='post', http_get='get', 'url_encode')
load('uuid', 'new_uuid')

DRATA_URL = 'https://public-api.drata.com'

# kwargs = {"access_secret":"75951deb-645b-4e63-b2d5-7471be61d210"}

# Can't be used because starlark does not support recursize function calls.
def flatten_json(json_obj, parent_key = "", sep = "."):
    items = {}
    for key, value in json_obj.items():
        if parent_key:
            new_key = '{}{}{}'.format(parent_key, sep, key) 
        else:
            new_key = key
        if type(value) == 'dict':
            items.update(flatten_json(value, new_key, sep=sep))
        else:
            items[new_key] = value
    return items

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
    token = kwargs['access_secret']
        
    # Get assets
    assets = []
    url = '{}/{}/'.format(DRATA_URL, 'public/assets')
    assets = http_get(url, headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if assets.status_code != 200:
        print('failed to retrieve assets')
        return None

    assets_json = json_decode(assets.body)['data']
    print(assets_json)

    assets_import = build_assets(assets_json)
    if not assets_import:
        print('no assets')
    
    return assets_import