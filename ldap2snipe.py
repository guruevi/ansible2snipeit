#!/usr/bin/env python3
import copy
from configparser import RawConfigParser
from os import getenv

from ldap.controls import SimplePagedResultsControl

import dns.resolver
import ldap
import logging

from snipeit_api.api import SnipeITApi
from snipeit_api.defaults import DEFAULTS
from snipeit_api.helpers import filter_list, get_dept_from_ou
from snipeit_api.models import Hardware

# Read in credentials from ini file
logging.basicConfig(level=logging.ERROR)
CONFIG = RawConfigParser()
logging.debug("Checking for a settings.conf ...")
CONFIG.read("settings.conf")
snipeit_apiurl = CONFIG.get('snipe-it', 'url')
snipeit_apikey = CONFIG.get('snipe-it', 'apikey')

entry = getenv('LDAP_CONFIG', 'ldap')
domain_creds = CONFIG[entry]

# Get this variable from environment
# snipeit_apikey =

domain = domain_creds['domain']
ldap_base = domain_creds['ldap_base']
ldap_bind_dn = domain_creds['bind_dn']
ldap_pass = domain_creds['password']
ldap_bases = domain_creds['search_bases'].split('\n')
ldap_filter = domain_creds['ldap_filter']

snipe_api = SnipeITApi(snipeit_apiurl, snipeit_apikey)


def process_result(item):
    ou = item['canonicalname'].split('/')[:-1]
    ou_text = "/".join(ou)

    new_hw: Hardware = (Hardware(api=snipe_api, custom_fields=copy.deepcopy(DEFAULTS['custom_fields']))
                        .get_by_name(item['cn'].upper())
                        .store_state())

    if not new_hw.id:
        return

    if new_hw.status_id == 1:
        new_hw.status_id = 2
    if new_hw.status_id == 5 or 'research' in ou_text.lower():
        new_hw.status_id = 4

    mgmt: list = new_hw.get_custom_field('Management').split(", ")
    new_hw.set_custom_field('Management', ", ".join(filter_list(mgmt + ['AD'])))

    domains: list = new_hw.get_custom_field('Domain').split(", ")
    new_hw.set_custom_field('Domain', ", ".join(filter_list(domains + [domain_creds['domain'].split('.')[0].upper()])))

    org_unit = ou_text.lower().replace('.rochester.edu', '')
    new_hw.set_custom_field('Org. Unit', org_unit)
    new_hw.set_custom_field("Department", get_dept_from_ou(org_unit))

    os: str = new_hw.get_custom_field('Operating System')
    if not os:
        new_hw.set_custom_field('Operating System', item['os'])

    os_version: str = new_hw.get_custom_field('OS Version')
    if not os_version:
        new_hw.set_custom_field('OS Version', item['os_version'])

    os_build: str = new_hw.get_custom_field('OS Build')
    if not os_build:
        new_hw.set_custom_field('OS Build', item['os_hotfix'] or item['os_servicepack'])

    new_hw.upsert()


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
    searchreq_attrlist = ["canonicalName", "cn", "operatingSystem", "OperatingSystemHotfix",
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
            if not isinstance(item[1], dict):
                continue
            for key in searchreq_attrlist:
                if key not in item[1]:
                    item[1][key] = ["".encode('utf-8')]

            result = {"canonicalname": item[1]["canonicalName"][0].decode("utf-8"),
                      "cn": item[1]["cn"][0].decode("utf-8").upper(),
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
