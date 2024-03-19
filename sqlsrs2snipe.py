#!/usr/bin/env python3
from __future__ import annotations

import copy
import logging
import os
from configparser import RawConfigParser
from datetime import datetime

from requests import get
from requests_ntlm import HttpNtlmAuth
from xmltodict import parse

from snipeit_api.api import SnipeITApi
from snipeit_api.defaults import DEFAULTS
from snipeit_api.helpers import clean_ip, clean_mac, filter_list, clean_tag, clean_user, print_progress
from snipeit_api.models import Hardware, Manufacturers, Models, Users

logging.basicConfig(level=logging.INFO)
CONFIG = RawConfigParser()
logging.debug("Checking for a settings.conf ...")
CONFIG.read("settings.conf")
snipeit_apiurl = CONFIG.get('snipe-it', 'url')
snipeit_apikey = CONFIG.get('snipe-it', 'apikey')
# Get the techs from the config file
DEFAULTS['techs'] = CONFIG.get('snipe-it', 'techs').split(" ")

snipe_api = SnipeITApi(url=snipeit_apiurl, api_key=snipeit_apikey)


def download_report(url, dest, auth_config=None):
    with open(dest, 'wb') as filedesc:
        dl = get(url, auth=auth_config)
        for chunk in dl.iter_content(chunk_size=512 * 1024):
            if chunk:  # filter out keep-alive new chunks
                filedesc.write(chunk)


def get_str(key, props):
    if key not in props or not props[key]:
        return ""
    if type(props[key]) is str or type(props[key]) is int:
        return str(props[key])
    if type(props[key]) is dict and "#text" in props[key]:
        return props[key]["#text"]
    return ""


def get_int(key, props):
    if key not in props or not props[key]:
        return 0
    if type(props[key]) is dict:
        if "#text" in props[key]:
            return parse_int(props[key]["#text"])
        # typically this is m:null="true"
        return 0
    return parse_int(props[key])


def parse_int(value):
    try:
        return int(value)
    except ValueError:
        return 0


# Stat file
try:
    report_stat = os.stat("./tmp/report_pc.xml")
except FileNotFoundError:
    report_stat = None

if (not report_stat or
        (datetime.now().timestamp() - report_stat.st_mtime) > CONFIG.get('sccm', 'max_age', fallback=86400)):
    # Get report
    report_pc = CONFIG.get('sccm', 'report_computers')
    report_net = CONFIG.get('sccm', 'report_network')
    report_edr = CONFIG.get('sccm', 'report_edr')
    auth = HttpNtlmAuth(CONFIG.get('sccm', 'username'), CONFIG.get('sccm', 'password'))

    # Get XML from response
    download_report(report_pc, "./tmp/report_pc.xml", auth)
    download_report(report_net, "./tmp/report_net.xml", auth)
    download_report(report_edr, "./tmp/report_edr.xml", auth)

# Open XML file
with open('./tmp/report_pc.xml') as fd:
    pc_doc = parse(fd.read())
with open('./tmp/report_net.xml') as fd:
    net_doc = parse(fd.read())
with open('./tmp/report_edr.xml') as fd:
    edr_doc = parse(fd.read())

PC_INFO = pc_doc['feed']['entry']
NET_XML = net_doc['feed']['entry']
EDR_XML = edr_doc['feed']['entry']
NET_INFO = {}
EDR_INFO = {}
# Convert NET_INFO into a dictionary of computer name -> ip, mac
for net_item in NET_XML:
    computer_name = get_str('d:Details_Table0_ComputerName', net_item['content']['m:properties']).split('.')[0]
    serial = get_str('d:Details_Table0_SerialNumber', net_item['content']['m:properties'])
    ip = clean_ip(net_item['content']['m:properties']['d:IP_Address'])
    mac = clean_mac(net_item['content']['m:properties']['d:MAC_Address'])
    computer_serial = computer_name + serial
    if computer_name not in NET_INFO:
        NET_INFO[computer_serial] = {'ip': [], 'mac': []}
    if ip:
        NET_INFO[computer_serial]['ip'].append(ip)
    if mac:
        NET_INFO[computer_serial]['mac'].append(mac)
for edr_item in EDR_XML:
    computer_name = edr_item['content']['m:properties']['d:Details_Table0_Netbios_Name0']
    if computer_name not in EDR_INFO:
        EDR_INFO[computer_name] = []
    EDR_INFO[computer_name] = ["CrowdStrike Falcon"]

print_progress(curr_pc := 0, total_pc := len(PC_INFO))
# For each entry tag
for entry in PC_INFO:
    updated = datetime.strptime(entry['updated'], "%Y-%m-%dT%H:%M:%SZ")
    # Get the properties
    properties = entry['content']['m:properties']
    asset_tag = clean_tag(get_str('d:Details_Table0_AssetTag', properties))
    if len(asset_tag) < 4:
        asset_tag = ""
    # Sometimes it is a FQDN, otherwise it is just computer
    computer_name = get_str('d:Details_Table0_ComputerName', properties).split('.')[0]
    serial_number = get_str('d:Details_Table0_SerialNumber', properties)
    computer_serial = computer_name + serial_number
    if len(computer_name) < 4:
        logging.warning(f"Skipping {computer_name} due to short name")
        continue
    if computer_serial not in NET_INFO or not NET_INFO[computer_serial]:
        logging.warning(f"Skipping {computer_name} due to no network information")
        continue
    if not NET_INFO[computer_serial]['mac'] and not serial_number:
        logging.warning(f"Skipping {computer_name} due to no MAC or serial number")
        continue
    if computer_name not in EDR_INFO or not EDR_INFO[computer_name]:
        EDR_INFO[computer_name] = []

    domain = get_str('d:Details_Table0_DomainWorkgroup', properties).split('.')[0]
    last_user = clean_user(get_str('d:Details_Table0_TopConsoleUser', properties))
    os = get_str('d:Details_Table0_OperatingSystem', properties).replace("Microsoft ", "")
    os_build = get_str('d:Details_Table0_ServicePackLevel', properties)
    model_name = get_str('d:Details_Table0_Model', properties).replace("Dell System ", "").replace("Dell ", "")

    NET_INFO[computer_serial]['mac'].sort()
    ip_address = ""
    if NET_INFO[computer_serial]['ip']:
        ip_address = sorted(NET_INFO[computer_serial]['ip'])[0]
    # Remove the last part of the string after the /
    ou = get_str('d:Details_Table0_OU', properties).lower().replace('.rochester.edu', '')
    if ou:
        ou = "/".join(ou.split("/")[:-1])

    model_config = {
        "manufacturer_id": DEFAULTS['manufacturer_id'],
        "category_id": DEFAULTS['category_id'],
        "fieldset_id": DEFAULTS['fieldset_id'],
        "eol": 0
    }
    # Mapping from SCCM (key) to Snipe-IT custom fields
    asset_config_nonauth = {
        "status_id": DEFAULTS['status_id_deployed'],
        "asset_tag": asset_tag or get_str('d:Details_Table0_ResourceID', properties),
        "_snipeit_ip_address_5": ip_address,
    }
    asset_config_auth = {
        "_snipeit_org_unit_26": ou,
        "_snipeit_os_type_17": "Windows" if "Windows" in os else "",
        "_snipeit_operating_system_14": os,
        "_snipeit_os_build_16": os_build,
        "_snipeit_cpu_18": get_str('d:Processor_Name', properties),
        "serial": serial_number,
    }

    # Remove empty values
    asset_config_nonauth = {k: v for k, v in asset_config_nonauth.items() if v}
    asset_config_auth = {k: v for k, v in asset_config_auth.items() if v}

    model_config['category_id'] = 3 if "server" in os.lower() else 2

    mfg_name = get_str('d:Details_Table0_Manufacturer', properties)
    manufacturer = Manufacturers(api=snipe_api, name=mfg_name).get_by_name().create()
    if 'dell' in mfg_name.lower():
        model_config['eol'] = 60  # 5 years
    if 'lenovo' in mfg_name.lower():
        model_config['eol'] = 36  # 3 years
    if 'hp' in mfg_name.lower():
        model_config['eol'] = 36  # 3 years
    if 'apple' in mfg_name.lower():
        model_config['eol'] = 84  # 7 years

    model_config['manufacturer_id'] = manufacturer.id

    model = Models(api=snipe_api, name=model_name).get_by_name().populate(model_config).create()
    asset_config_auth['model_id'] = model.id or DEFAULTS['model_id']

    assert asset_config_auth['model_id'] != 0

    new_hw = (Hardware(api=snipe_api,
                       asset_tag=asset_config_nonauth['asset_tag'],
                       name=computer_name,
                       serial=serial_number,
                       model_id=model.id,
                       custom_fields=copy.deepcopy(DEFAULTS['custom_fields']))
              .populate(asset_config_nonauth)
              .get_by_assettag()
              .get_by_serial()
              .get_by_mac(filter_list(NET_INFO[computer_serial]['mac']))
              .store_state())

    if new_hw.serial and clean_tag(serial_number) and new_hw.serial != serial_number:
        # We likely matched on a duplicate MAC address but the serial number is different
        logging.error(f"Serial number mismatch for {computer_name}: {new_hw.serial} != {serial_number}")
        print(filter_list(NET_INFO[computer_serial]['mac']))
        continue

    # Populate all the custom fields
    new_hw.populate(asset_config_auth).populate_mac(filter_list(NET_INFO[computer_serial]['mac']))

    # Storage and RAM sometimes fluctuate after upgrades, pick the bigger one if a value already exists
    new_storage = get_int('d:Details_Table0_DiskSpaceMB', properties)
    if new_hw.get_custom_field("Storage"):
        current_storage = parse_int(new_hw.get_custom_field("Storage"))
        if current_storage < new_storage:
            new_hw.set_custom_field("Storage", new_storage)
    else:
        new_hw.set_custom_field("Storage", new_storage)

    new_ram = round(get_int('d:Details_Table0_MemoryKBytes', properties) / 1024)
    if new_hw.get_custom_field("RAM"):
        current_ram = parse_int(new_hw.get_custom_field("RAM"))
        if current_ram < new_ram:
            new_hw.set_custom_field("RAM", new_ram)
    else:
        new_hw.set_custom_field("RAM", new_ram)

    # Amend domain
    old_domain = []
    if new_hw.get_custom_field("Domain"):
        old_domain = new_hw.get_custom_field("Domain").split(", ")
    new_domain = []
    if domain:  # Sometimes it is empty
        new_domain = [domain.upper()]
    new_hw.set_custom_field("Domain", ", ".join(filter_list(new_domain + old_domain)))
    domain = new_hw.get_custom_field("Domain")

    # We are always deployed (SCCM)
    if new_hw.status_id == DEFAULTS['status_id_pending'] and 'UR' in domain:
        new_hw.status_id = DEFAULTS['status_id_deployed']
    if 'UR' in domain and 'research' in ou.lower():
        # 4 is Research (Compliant)
        new_hw.status_id = 4
    elif 'research' in ou.lower() or 'CTCC' in domain or 'HEART' in domain:
        # 5 is Research (Non-Compliant)
        new_hw.status_id = 5

    management = ['SCCM']
    if 'UR' in domain:
        management.append('AD')
    old_management = new_hw.get_custom_field("Management")
    if not old_management:
        # Filter list to remove empty, duplicate values and sort in order
        new_hw.set_custom_field("Management", ', '.join(filter_list(management)))
    else:
        old_management_list = old_management.split(", ")
        # Add the new values to the old values
        new_hw.set_custom_field("Management", ', '.join(filter_list(old_management_list + management)))

    if not new_hw.get_custom_field("EDR"):
        new_hw.set_custom_field("EDR", ", ".join(EDR_INFO[computer_name]))
    else:
        # Add the new values to the old values
        new_hw.set_custom_field("EDR", ', '.join(
            filter_list(new_hw.get_custom_field("EDR").split(", ") + EDR_INFO[computer_name])))

    logging.debug(new_hw.to_dict() | new_hw.get_custom_fields())

    # Make sure to filter out the unknowns but maintain the domain
    if last_user:
        # Set the raw value for last user
        new_hw.set_custom_field("Last User", last_user)
        # Users will strip the domain
        user = Users(api=snipe_api, username=last_user).get_by_username()
        if user.id:
            if user.department and not new_hw.get_custom_field("Department"):
                new_hw.set_custom_field("Department", user.department.name)
            if user.department not in DEFAULTS['techs'] and user.username not in DEFAULTS['techs']:
                if new_hw.status_id == DEFAULTS['status_id_deployed'] or new_hw.status_id == 4:
                    try:
                        new_hw.upsert().checkout_to_user(user, note="From SCCM")
                    except ValueError:
                        logging.error(f"Failed to check out {new_hw.name} to {user.username}")
            # If we have an empty department, then update it

    # Putting it here avoids the duplicate calls when we have a user
    new_hw.upsert()
    print_progress(curr_pc, total_pc)
    curr_pc += 1
