#!/usr/bin/env python3
from __future__ import annotations

import copy
import logging
import os
from configparser import RawConfigParser
from datetime import datetime
import concurrent.futures
from requests import get
from requests_ntlm import HttpNtlmAuth
from xmltodict import parse

from snipeit_api.api import SnipeITApi
from snipeit_api.defaults import DEFAULTS
from snipeit_api.helpers import clean_ip, clean_mac, filter_list, clean_tag, clean_user, print_progress, \
    get_dept_from_ou, validate_os
from snipeit_api.models import Hardware, Manufacturers, Models

logging.basicConfig(level=logging.INFO)
CONFIG = RawConfigParser()
CONFIG.read("settings.conf")
snipeit_apiurl = CONFIG.get('snipe-it', 'url')
snipeit_apikey = CONFIG.get('snipe-it', 'apikey')
DEFAULTS['techs'] = CONFIG.get('snipe-it', 'techs').split(" ")

snipe_api = SnipeITApi(url=snipeit_apiurl, api_key=snipeit_apikey)


def download_report(url, dest, auth_config=None):
    with open(dest, 'wb') as filedesc:
        dl = get(url, auth=auth_config)
        for chunk in dl.iter_content(chunk_size=512 * 1024):
            if chunk:
                filedesc.write(chunk)


def get_str(key, props):
    value = props.get(key, "")
    if isinstance(value, (str, int)):
        return str(value)
    if isinstance(value, dict) and "#text" in value:
        return value["#text"]
    return ""


def get_int(key, props):
    value = props.get(key, 0)
    if isinstance(value, dict) and "#text" in value:
        return parse_int(value["#text"])
    return parse_int(value)


def parse_int(value):
    try:
        return int(value)
    except ValueError:
        return 0


def load_xml(file_path):
    with open(file_path) as fd:
        return parse(fd.read())['feed']['entry']


def process_network_info(net_xml):
    net_info = {}
    for net_item in net_xml:
        properties = net_item['content']['m:properties']
        computer_name = get_str('d:Details_Table0_ComputerName', properties).split('.')[0].upper()
        serial = get_str('d:Details_Table0_SerialNumber', properties).upper()
        ip = clean_ip(properties['d:IP_Address'])
        mac = clean_mac(properties['d:MAC_Address'])
        computer_serial = computer_name + serial
        if computer_serial not in net_info:
            net_info[computer_serial] = {'ip': [], 'mac': []}
        if ip:
            net_info[computer_serial]['ip'].append(ip)
        if mac:
            net_info[computer_serial]['mac'].append(mac)
    return net_info


def process_edr_info(edr_xml):
    edr_info = {}
    for edr_item in edr_xml:
        computer_name = edr_item['content']['m:properties']['d:Details_Table0_Netbios_Name0'].split('.')[0].upper()
        edr_info[computer_name] = ["CrowdStrike Falcon"]
    return edr_info


def process_entry(properties, net_info, edr_info, api: SnipeITApi):
    computer_name = get_str('d:Details_Table0_ComputerName', properties).split('.')[0].upper()
    serial_number = get_str('d:Details_Table0_SerialNumber', properties).upper()
    computer_serial = computer_name + serial_number

    if len(computer_name) < 4 or computer_serial not in net_info or not net_info[computer_serial]['mac']:
        logging.warning(f"Skipping {computer_name} due to insufficient data")
        return

    asset_tag = clean_tag(get_str('d:Details_Table0_AssetTag', properties))
    domain = get_str('d:Details_Table0_DomainWorkgroup', properties).split('.')[0]
    last_user = clean_user(get_str('d:Details_Table0_TopConsoleUser', properties))
    operating_system = get_str('d:Details_Table0_OperatingSystem', properties)
    os_build = get_str('d:Details_Table0_ServicePackLevel', properties)
    model_name = get_str('d:Details_Table0_Model', properties).replace("Dell System ", "").replace("Dell ", "")

    ip_address = sorted(net_info[computer_serial]['ip'])[0] if net_info[computer_serial]['ip'] else ""
    ou = "/".join(get_str('d:Details_Table0_OU', properties).lower().replace('.rochester.edu', '').split("/")[:-1])

    asset_config_nonauth = {
        "status_id": DEFAULTS['status_id_deployed'],
        "asset_tag": asset_tag or get_str('d:Details_Table0_ResourceID', properties),
        "_snipeit_ip_address_5": ip_address,
    }
    asset_config_auth = {
        "_snipeit_os_type_17": "Windows",
        "_snipeit_operating_system_14": validate_os(operating_system),
        "_snipeit_os_build_16": os_build,
        "_snipeit_cpu_18": get_str('d:Processor_Name', properties),
        "serial": serial_number,
    }

    asset_config_nonauth = {k: v for k, v in asset_config_nonauth.items() if v}
    asset_config_auth = {k: v for k, v in asset_config_auth.items() if v}

    model_config = {
        "manufacturer_id": DEFAULTS['manufacturer_id'],
        "category_id": 3 if "server" in operating_system.lower() else 2,
        "fieldset_id": DEFAULTS['fieldset_id'],
        "eol": 0
    }

    mfg_name = get_str('d:Details_Table0_Manufacturer', properties)
    manufacturer = Manufacturers(api=api, name=mfg_name).get_by_name().create()
    model_config[
        'eol'] = 60 if 'dell' in mfg_name.lower() else 36 if 'lenovo' in mfg_name.lower() or 'hp' in mfg_name.lower() else 84 if 'apple' in mfg_name.lower() else 0
    model_config['manufacturer_id'] = manufacturer.id

    model = Models(api=api, name=model_name).get_by_name().populate(model_config).create()
    asset_config_auth['model_id'] = model.id or DEFAULTS['model_id']
    assert asset_config_auth['model_id'] != 0

    new_hw = (Hardware(api=api,
                       asset_tag=asset_config_nonauth['asset_tag'],
                       name=computer_name,
                       serial=serial_number,
                       model_id=model.id,
                       custom_fields=copy.deepcopy(DEFAULTS['custom_fields']))
              .populate(asset_config_nonauth)
              .get_by_serial()
              .get_by_mac(filter_list(net_info[computer_serial]['mac']))
              .get_by_asset_tag()
              .get_by_name()
              .store_state())

    if new_hw.serial and clean_tag(serial_number) and new_hw.serial != serial_number:
        logging.error(f"Serial number mismatch for {computer_name}: {new_hw.serial} != {serial_number}")
        logging.error(filter_list(net_info[computer_serial]['mac']))
        return

    new_hw.populate(asset_config_auth).populate_mac(filter_list(net_info[computer_serial]['mac']))

    new_storage = get_int('d:Details_Table0_DiskSpaceMB', properties)
    current_storage = parse_int(new_hw.get_custom_field("Storage"))
    if current_storage < new_storage:
        new_hw.set_custom_field("Storage", new_storage)

    new_ram = round(get_int('d:Details_Table0_MemoryKBytes', properties) / 1024)
    current_ram = parse_int(new_hw.get_custom_field("RAM"))
    if current_ram < new_ram:
        new_hw.set_custom_field("RAM", new_ram)

    old_domain = new_hw.get_custom_field("Domain").split(", ")
    new_domain = [domain.upper()] if domain else []
    new_hw.set_custom_field("Domain", ", ".join(filter_list(new_domain + old_domain)))

    management = ['SCCM']
    if 'UR' in domain:
        management.append('AD')
    old_management = new_hw.get_custom_field("Management").split(', ')
    new_hw.set_custom_field("Management", ', '.join(filter_list(old_management + management)))

    edr = new_hw.get_custom_field("EDR").split(', ')
    new_hw.set_custom_field("EDR", ', '.join(filter_list(edr + edr_info.get(computer_name, []))))

    if ou:
        new_hw.set_custom_field("Org. Unit", ou)
        new_hw.set_custom_field("Department", get_dept_from_ou(ou))

    if last_user:
        new_hw.set_custom_field("Last User", last_user)

    try:
        new_hw.upsert()
    except ValueError:
        logging.error(f"Failed to upsert {new_hw.name} (duplicate Asset Tag?)")


def main():
    report_stat = os.stat("./tmp/report_pc.xml") if os.path.exists("./tmp/report_pc.xml") else None
    if not report_stat or (datetime.now().timestamp() - report_stat.st_mtime) > CONFIG.get('sccm', 'max_age',
                                                                                           fallback=86400):
        auth = HttpNtlmAuth(CONFIG.get('sccm', 'username'), CONFIG.get('sccm', 'password'))
        download_report(CONFIG.get('sccm', 'report_computers'), "./tmp/report_pc.xml", auth)
        download_report(CONFIG.get('sccm', 'report_network'), "./tmp/report_net.xml", auth)
        download_report(CONFIG.get('sccm', 'report_edr'), "./tmp/report_edr.xml", auth)

    pc_info = load_xml('./tmp/report_pc.xml')
    net_info = process_network_info(load_xml('./tmp/report_net.xml'))
    edr_info = process_edr_info(load_xml('./tmp/report_edr.xml'))
    total_entries = len(pc_info)
    completed_entries = 0
    for entry in pc_info:
        process_entry(entry['content']['m:properties'], net_info, edr_info, snipe_api)
        completed_entries += 1
        print_progress(completed_entries, total_entries)


if __name__ == "__main__":
    main()
