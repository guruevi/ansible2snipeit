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
from snipeit_api.helpers import filter_list, get_dept_from_ou, clean_user
from snipeit_api.models import Hardware, Users, Departments

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
ldap_bind_dn = domain_creds['bind_dn']
ldap_pass = domain_creds['password']
ldap_bases = domain_creds['search_bases'].split('\n')
ldap_user_base = domain_creds['ldap_base']
ldap_filter_computer = domain_creds['ldap_filter']
ldap_filter_user = domain_creds['ldap_filter_user']

snipe_api = SnipeITApi(snipeit_apiurl, snipeit_apikey)


def process_computer(item):
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


def process_user(item: dict, manager_lookup: dict[str, str]):
    username = clean_user(item['username'])
    uidnumber = int(item['uidnumber'])

    if not int(item['uidnumber']) or not username:
        return

    new_user = Users(api=snipe_api).get_by_employee_num(uidnumber)

    new_user.store_state()

    # This is a new user, make sure we have a username
    if not new_user.id:
        new_user.username = username
        new_user.first_name = item['given_name']
        new_user.last_name = item['sn']
        new_user.employee_num = uidnumber

    if not new_user.first_name:
        new_user.first_name = username
    if not new_user.last_name:
        new_user.last_name = 'Unknown'

    if item['mail'] and not new_user.email:
        new_user.email = item['mail']
    if item['title'] and not new_user.jobtitle:
        new_user.jobtitle = item['title']
    if item['telephone_number'] and not new_user.phone:
        new_user.phone = item['telephone_number']


    department_name = item['department'].strip()
    if department_name and not new_user.department_id:
        department = Departments(api=snipe_api, name=department_name).get_by_name()
        if not department.id:
            logging.info(f"Could not find department {department_name}")
            department.create()
        if department.id:
            new_user.department_id = department.id

    manager_uid = manager_lookup.get(item['manager_dn'].lower(), '')
    if manager_uid and manager_uid != new_user.employee_num:
        manager = Users(api=snipe_api).get_by_employee_num(manager_uid)
        if manager.id:
            new_user.manager_id = manager.id

    try:
        new_user.upsert()
    except ValueError as e:
        logging.error(f"Error upserting {new_user.username}: {e}")


def _decode_attr(attrs: dict, key: str) -> str:
    if key not in attrs or not attrs[key]:
        return ''
    return attrs[key][0].decode('utf-8').strip()


def query_base(ldap_conn, ldap_base, searchreq_attrlist, ldap_filter):
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

    req_ctrl = SimplePagedResultsControl(criticality=True, size=page_size, cookie='')
    msgid = ldap_conn.search_ext(base=ldap_base,
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

            results.append(item)

        pctrls = [c for c in serverctrls if c.controlType == SimplePagedResultsControl.controlType]
        if not pctrls or not pctrls[0].cookie:
            break

        req_ctrl.cookie = pctrls[0].cookie
        msgid = ldap_conn.search_ext(base=ldap_base, scope=ldap.SCOPE_SUBTREE, filterstr=ldap_filter,
                                     attrlist=searchreq_attrlist, serverctrls=[req_ctrl])

    return results

def connect_ldap():
    # Query DNS for nearest LDAP server
    ldap_server = dns.resolver.resolve(f'_ldap._tcp.{domain}', 'SRV')[0].target.to_text()

    # Connect to LDAP
    ldap_conn = ldap.initialize(f"ldap://{ldap_server}")
    ldap_conn.protocol_version = 3
    ldap_conn.set_option(ldap.OPT_REFERRALS, 0)
    ldap_conn.simple_bind_s(ldap_bind_dn, ldap_pass)
    return ldap_conn

def get_host():
    ldap_conn = connect_ldap()
    # Search for all hosts How many users to search for in each page, this depends on the server maximum setting
    # (by default the highest value is 1000)
    for current_ldap_base in ldap_bases:
        results = query_base(ldap_conn, current_ldap_base, ["canonicalName", "cn", "operatingSystem", "OperatingSystemHotfix",
                          "OperatingSystemServicePack", "operatingSystemVersion"], ldap_filter_computer)

        for item in results:
            result = {"canonicalname": item[1]["canonicalName"][0].decode("utf-8"),
                      "cn": item[1]["cn"][0].decode("utf-8").upper(),
                      "os": item[1]["operatingSystem"][0].decode("utf-8"),
                      "os_hotfix": item[1]["OperatingSystemHotfix"][0].decode("utf-8"),
                      "os_servicepack": item[1]["OperatingSystemServicePack"][0].decode("utf-8"),
                      "os_version": item[1]["operatingSystemVersion"][0].decode("utf-8")}
            process_computer(result)

def get_user():
    ldap_conn = connect_ldap()
    search_attrs = [
        "sn", "sAMAccountName", "givenName", "mail", "department", "title", "manager",
        "telephoneNumber", "uidNumber", "distinguishedName"
    ]
    results = query_base(ldap_conn, ldap_user_base, search_attrs, ldap_filter_user)

    users = []
    manager_lookup = {}

    for item in results:
        attrs = item[1]
        result = {
            "sn": _decode_attr(attrs, "sn"),
            "username": _decode_attr(attrs, "sAMAccountName"),
            "given_name": _decode_attr(attrs, "givenName"),
            "mail": _decode_attr(attrs, "mail"),
            "department": _decode_attr(attrs, "department"),
            "title": _decode_attr(attrs, "title"),
            "manager_dn": _decode_attr(attrs, "manager"),
            "telephone_number": _decode_attr(attrs, "telephoneNumber"),
            "uidnumber": _decode_attr(attrs, "uidNumber"),
            "distinguished_name": _decode_attr(attrs, "distinguishedName")
        }
        users.append(result)

        manager_key = result['distinguished_name'].lower()
        manager_uid = result['uidnumber']
        if manager_key and manager_uid:
            manager_lookup[manager_key] = manager_uid

    for user in users:
        process_user(user, manager_lookup)


def main():
    get_host()
    get_user()


if __name__ == '__main__':
    main()
