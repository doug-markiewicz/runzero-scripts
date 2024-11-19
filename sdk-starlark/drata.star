# runZero Starlark script for Drata
# Last updated 11/14/2024
# NOTE: Still need to add parsing for assetClassType and complianceChecks

load('runzero.types', 'ImportAsset', 'NetworkInterface')
load('json', json_encode='encode', json_decode='decode')
load('net', 'ip_address')
load('http', http_post='post', http_get='get', 'url_encode')
load('uuid', 'new_uuid')

DRATA_URL = 'https://public-api.drata.com'

def build_assets(assets_json):
    assets_import = []
    for item in assets_json:
        id = item.get('id', new_uuid) 
        hostname = item.get('name', '')
        description = item.get('description', '')
        asset_type = item.get('assetType', '')
        asset_provider = item.get('assetProvider', '')
        employment_status = item.get('employmentStatus', '')
        created_at = item.get('createdAt', '')
        updated_at = item.get('updatedAt', '')
        removed_at = item.get('removedAt', '')

        ips = ['127.0.0.1']
        macs = []
        if macs:
            #for m in macs:
            network = build_network_interface(ips=ips, mac=macs)
        else:
            network = build_network_interface(ips=ips, mac=None)

        device = []
        device = item.get('device', {})
        if device:
            os_version = device.get('osVersion', '')
            serial_number = device.get('serialNumber', '')
            model = device.get('model', '')
            agent_version = device.get('agentVersion', '')
            macs = device.get('macAddress', [])
            encryption_enabled = device.get('encryptionEnabled', '')
            firewall_enabled = device.get('firewallEnabled', '')
            gatekeeper_enabled = device.get('gateKeeperEnabled', '')
            last_checked_at = device.get('lastCheckedAt', '')
            source_type = device.get('sourceType', '')
            created_at = device.get('createdAt', '')
            updated_at = device.get('updatedAt', '')
            deleted_at = device.get('deletedAt', '')
            apps_count = device.get('appsCount', '')
            is_device_compliant = device.get('isDeviceCompliant', '')
            compliance_checks = device.get('complianceChecks', {})

        owner = []
        owner = item.get('owner', {})
        if owner:
            owner_id = owner.get('id', '')
            owner_email = owner.get('email', '')
            owner_first_name = owner.get('firstName', '')
            owner_last_name = owner.get('lastName', '')
            owner_terms_agreed = owner.get('drataTermsAgreedAt', '')
            owner_created_at = owner.get('createdAt', '')
            owner_updated_at = owner.get('updatedAt', '')
            owner_roles = owner.get('roles', [])

        # handle additional attributes collected for asset
        custom_attrs = {}
        custom_attribs_to_ignore = []

        for key, value in item.items():
            if type(value) != 'dict':
                if key not in custom_attribs_to_ignore:
                    custom_attrs[key] = str(value)[:1023]

        assets_import.append(
            ImportAsset(
                id=str(id),
                hostnames=[hostname],
                networkInterfaces=[network],
                os=os_version,
                customAttributes={
                    "description":description,
                    "assetType":asset_type,
                    "asset_provider":asset_provider,
                    "employmentStatus":employment_status,
                    "createdAt":created_at,
                    "updatedAt":updated_at,
                    "removedAt":removed_at,
                    "device.os":os_version,
                    "device.serialNumber":serial_number,
                    "device.model":model,
                    "device.agentVersion":agent_version,
                    "device.macs":macs,
                    "device.encryptionEnabled":encryption_enabled,
                    "device.firewallEnabled":firewall_enabled,
                    "device.gatekeeperEnabled":gatekeeper_enabled,
                    "device.lastCheckedAat":last_checked_at,
                    "device.sourceType":source_type,
                    "device.createdAt":created_at,
                    "device.updatedAt":updated_at,
                    "device.deletedAt":deleted_at,
                    "device.appsCount":apps_count,
                    "device.isDeviceCompliant":is_device_compliant,
                    "device.complianceChecks":[compliance_checks],
                    "owner.id":owner_id,
                    "owner.email":owner_email,
                    "owner.firstName":owner_first_name,
                    "owner.lastName":owner_last_name,
                    "owner.drataTermsAgreedAt":owner_terms_agreed,
                    "owner.createdAt":owner_created_at,
                    "owner.updatedAt":owner_updated_at,
                    "owner.roles":[owner_roles]
                }
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
    filter = 'assetClassType=HARDWARE&employmentStatus=CURRENT_EMPLOYEE'
    
    page = 1
    page_size = 50
    hasNextPage = True
    
    while hasNextPage:
        url = '{}/{}?{}&page={}&limit={}'.format(DRATA_URL, 'public/assets', filter, page, page_size)
        results = http_get(url, headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
        if results.status_code != 200:
            print('failed to retrieve assets')
            return None
        
        total = json_decode(results.body)['total']

        if total == 9999999:
            results_json = json_decode(results.body)['data']
            assets.extend(results_json)
            page += 1
        elif total == 0:
            hasNextPage = False
        else:
            print('unexpected value returned for total')
            hasNextPage = False

    assets_import = build_assets(assets)
    if not assets_import:
        print('no assets')

    return assets_import