load('runzero.types', 'ImportAsset', 'NetworkInterface')
load('json', json_encode='encode', json_decode='decode')
load('net', 'ip_address')
load('http', http_post='post', http_get='get', 'url_encode')
load('uuid', 'new_uuid')

DIGITAL_OCEAN_OAUTH_URL = 'https://cloud.digitalocean.com/v1/'
DIGITAL_OCEAN_API_URL = 'https://api.digitalocean.com/v2/'
RUNZERO_REDIRECT = 'https://console.runzero.com/'

def build_assets(assets_json):
    assets_import = []
    for item in assets_json:
        id = item.get('id', new_uuid)      
        hostname = item.get('name', '')
        memory = item.get('memory', '')
        vcpus = item.get('vcpus', '')
        disk = item.get('disk','')
        locked = item.get('locked', '')
        status = item.get('status', '')
        created_at = item.get('created_at', '')
        vpc_uuid = item.get('vpc_uuid', '')
        size_slug = item.get('size_slug', '')

        # parse IP addresses
        ipv4s = []
        ipv6s = []
        ips = []
        networks = item.get('networks', {})
        if networks:
            ipv4s = networks.get('v4', [])
            ipv6s = networks.get('v6', [])
            
            if ipv4s:
                for v4 in ipv4s:
                    addr = v4.get('ip_address', '')
                    ips.append(addr)
        
            if ipv6s:
                for v6 in ipv6s:
                    addr = v6.get('ip_address', '')
                    ips.append(addr)        

        network = build_network_interface(ips=ips, mac=None)

        # parse image information
        image = item.get('image', {})
        if image:
            image_id = image.get('id', '')
            image_name = image.get('name','')
            image_distribution = image.get('distribution', '')
            image_type = image.get('type', '')
            image_public = image.get('public', '')
            image_status = image.get('status', '')

        # parse region information
        region = item.get('region', {})
        if region:
            region_name = region.get('name', '')
            region_features = region.get('features', '')
            region_available = region.get('available', '')

        # parse tags
        tags_rz = []
        tags_do = item.get('tags', [])
        if tags_do:
            for t in tags_do:
                if ':' in t:
                    key, value = t.split(':', 1)
                    tags_rz.append(key + '=' + value)
                else:
                    key = t
                    tags_rz.append(key)
                
        assets_import.append(
            ImportAsset(
                id=str(id),
                hostnames=[hostname],
                networkInterfaces=[network],
                os=image_distribution,
                customAttributes={
                    "id":id,
                    "size_slug":size_slug,
                    "memory":memory,
                    "vcpus":vcpus,
                    "disk":disk,
                    "locked":locked,
                    "status":status,
                    "created_at":created_at,
                    "vpcUUID":vpc_uuid,
                    "image.id":image_id,
                    "image.name":image_name,
                    "image.distribution":image_distribution,
                    "image.type":image_type,
                    "image.public":image_public,
                    "image.status":image_status,
                    "region.name":region_name,
                    "region.features":region_features,
                    "region.available":region_available,
                    "tags":tags_rz
                }
            )
        )
    return assets_import

# build runZero network interfaces; shouldn't need to touch this
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
    # kwargs!!
    token = kwargs['access_secret']

    # get assets
    assets = []
    url = '{}/{}'.format(DIGITAL_OCEAN_API_URL, 'droplets')
    assets = http_get(url, headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    if assets.status_code != 200:
        print('failed to retrieve assets' + assets)
        return None

    assets_json = json_decode(assets.body)['droplets']

    # build asset import
    assets_import = build_assets(assets_json)
    if not assets_import:
        print('no assets')
    
    return assets_import