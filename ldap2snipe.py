#!/usr/bin/env python3
import ipaddress

from ldap.controls import SimplePagedResultsControl

import dns.resolver
import ldap

from ansible2snipe import CONFIG, get_snipe_asset, create_snipe_asset, update_snipe_asset, logging

# Read in credentials from ini file
domain_creds = CONFIG['ldap']

domain = domain_creds['domain']
ldap_base = domain_creds['ldap_base']
ldap_bind_dn = domain_creds['bind_dn']
ldap_pass = domain_creds['password']
ldap_bases = domain_creds['search_bases'].split('\n')
ldap_filter = domain_creds['ldap_filter']


def process_result(item):
    logging.debug(item)

    ou = item['canonicalname'].split('/')[:-1]
    ou_text = "/".join(ou)
    payload = {"name": item['cn'].upper(),
               '_snipeit_operating_system_8': item['os'],
               '_snipeit_domain_11': domain_creds['domain'].split('.')[0].upper(),
               '_snipeit_ou_12': ou_text,
               '_snipeit_os_version_9': item['os_version'],
               '_snipeit_os_build_10': item['os_hotfix'] or item['os_servicepack'],
               }

    # Validate IP addresses
    try:
        payload['_snipeit_ip_address_13'] = str(ipaddress.ip_address(item['ipaddress']))
    except (ValueError, KeyError):
        print(f"Error: {payload['name']} has no correct IP address.")

    asset_tag = "LDAP-{}".format(item['cn'].upper())
    assets = get_snipe_asset(name=item['cn'].upper(), asset_tag=asset_tag)
    if assets['total'] == 0:
        logging.info(f"No assets found, creating {item['cn']}")
        payload['category_id'] = 2
        payload['status_id'] = 2
        payload['model_id'] = 11
        payload['asset_tag'] = asset_tag
        create_snipe_asset(payload)
        return
    elif assets['total'] > 1:
        logging.error(f"More than one asset found {item['cn']}")
        return

    logging.debug(assets['rows'][0])
    # Make Pending to Ready to Deploy
    if assets['rows'][0]['status_label']['id'] == 1:
        payload['status_id'] = 2
    # Do not update certain values if something else already set them
    if assets['rows'][0]['custom_fields']['OS Version']['value']:
        del payload['_snipeit_os_version_9']
    if assets['rows'][0]['custom_fields']['OS Build']['value']:
        del payload['_snipeit_os_build_10']
    if assets['rows'][0]['custom_fields']['Operating System']['value']:
        del payload['_snipeit_operating_system_8']

    update_snipe_asset(assets['rows'][0], payload)


def query_base(ldap_conn, current_ldap_base):
    # Search for all hosts
    # How many users to search for in each page, this depends on the server maximum setting
    # (by default the highest value is 1000)
    page_size = 500
    # Get attributes
    # CanonicalName                        : domain/ou/ou/cn
    # CN                                   : hostname
    # IPv4Address                          : ipaddress
    # OperatingSystem                      : Windows Server 2016 Standard
    # OperatingSystemHotfix                :
    # OperatingSystemServicePack           :
    # OperatingSystemVersion               :
    searchreq_attrlist = ["canonicalName", "cn", "IPv4Address", "operatingSystem", "OperatingSystemHotfix",
                          "OperatingSystemServicePack", "operatingSystemVersion"]
    req_ctrl = SimplePagedResultsControl(criticality=True, size=page_size, cookie='')
    msgid = ldap_conn.search_ext(base=current_ldap_base,
                                 scope=ldap.SCOPE_SUBTREE,
                                 filterstr=ldap_filter,
                                 attrlist=searchreq_attrlist, serverctrls=[req_ctrl])

    results = []
    # Loop over all the pages using the same cookie, otherwise the search will fail
    while True:
        _, rdata, _, serverctrls = ldap_conn.result3(msgid)
        for item in rdata:
            logging.debug(item[1])
            for key in searchreq_attrlist:
                if key not in item[1]:
                    item[1][key] = ["".encode('utf-8')]

            result = {"canonicalname": item[1]["canonicalName"][0].decode("utf-8"),
                      "cn": item[1]["cn"][0].decode("utf-8").upper(),
                      "ipaddress": item[1]["IPv4Address"][0].decode("utf-8"),
                      "os": item[1]["operatingSystem"][0].decode("utf-8"),
                      "os_hotfix": item[1]["OperatingSystemHotfix"][0].decode("utf-8"),
                      "os_servicepack": item[1]["OperatingSystemServicePack"][0].decode("utf-8"),
                      "os_version": item[1]["operatingSystemVersion"][0].decode("utf-8")}

            results.append(result)

        pctrls = [c for c in serverctrls if c.controlType == SimplePagedResultsControl.controlType]
        if not pctrls or not pctrls[0].cookie:
            break

        req_ctrl.cookie = pctrls[0].cookie
        msgid = ldap_conn.search_ext(base=current_ldap_base, scope=ldap.SCOPE_SUBTREE, filterstr=ldap_filter,
                                     attrlist=searchreq_attrlist, serverctrls=[req_ctrl])

    for result in results:
        process_result(result)

    return None


def get_host():
    # Query Active Directory for all hosts
    # Query DNS for nearest LDAP server
    ldap_server = dns.resolver.resolve(f'_ldap._tcp.{domain}', 'SRV')[0].target.to_text()

    # Connect to LDAP
    ldap_conn = ldap.initialize(f"ldap://{ldap_server}")
    ldap_conn.protocol_version = 3
    ldap_conn.set_option(ldap.OPT_REFERRALS, 0)
    ldap_conn.simple_bind_s(ldap_bind_dn, ldap_pass)
    # Search for all hosts How many users to search for in each page, this depends on the server maximum setting
    # (by default the highest value is 1000)
    for current_ldap_base in ldap_bases:
        query_base(ldap_conn, current_ldap_base)


def main():
    get_host()


if __name__ == '__main__':
    main()
