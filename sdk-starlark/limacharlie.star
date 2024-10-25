load('runzero.types', 'ImportAsset', 'NetworkInterface')
load('json', json_encode='encode', json_decode='decode')
load('net', 'ip_address')
load('http', http_post='post', http_get='get', 'url_encode')
load('uuid', 'new_uuid')

LIMACHARLIE_JWT_URL = 'https://jwt.limacharlie.io'
LIMACHARLIE_BASE_URL = 'https://api.limacharlie.io/v1'

def get_token(oid, access_token):
    url = '{}/?oid={}&secret={}'.format(LIMACHARLIE_JWT_URL, oid, access_token)
    token = http_post(url, headers={"Content-Type": "application/json"})
    if token.status_code != 200:
        return None
    token_json = json_decode(token.body)
    return token_json['jwt']

def build_assets(sensors):
    assets = []
    for item in sensors:
        sid = item.get('sid', new_uuid)        
        hostname = item.get('hostname', '')

        ips = []
        int_ip = item.get('int_ip', '')
        if int_ip:
            ips.append(int_ip)
        ext_ip = item.get('ext_ip', '')
        if ext_ip:
            ips.append(ext_ip)

        mac = item.get('mac_addr', '')
        if mac:
            mac = mac.replace("-", ":")
            network = build_network_interface(ips=ips, mac=mac)
        else:
            network = build_network_interface(ips=ips, mac=None)

        # handle additional attributes collected for asset
        custom_attrs = {}

        custom_attribs_to_ignore = [
            "sid",
            "hostname",
            "mac_addr",
            "int_ip",
            "ext_ip"
        ]

        for key, value in item.items():
            if type(value) != 'dict':
                if key not in custom_attribs_to_ignore:
                    custom_attrs[key] = str(value)[:1023]

        assets.append(
            ImportAsset(
                id=sid,
                hostnames=[hostname],
                networkInterfaces=[network],
                customAttributes=custom_attrs
            )
        )
    return assets

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
    oid = kwargs['access_key']
    access_token = kwargs['access_secret']
    token = get_token(oid, access_token)
    if not token:
        print('failed to get token')
        return None
        
    # Get sensors
    url = '{}/{}/{}'.format(LIMACHARLIE_BASE_URL, 'sensors', oid)
    sensors = http_get(url, headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if sensors.status_code != 200:
        print('failed to retrieve sensors')
        return None

    sensors_json = json_decode(sensors.body)['sensors']

    assets = build_assets(sensors_json)
    if not assets:
        print('no assets')
    
    return assets