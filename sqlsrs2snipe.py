#!/usr/bin/env python3
# Open XML file
import html
from datetime import datetime
import logging
import os
import xml.etree.ElementTree as ElementTree

import requests
from requests_ntlm import HttpNtlmAuth
from ansible2snipe import (get_snipe_model_id, get_snipe_asset, clean_tag, create_snipe_asset, update_snipe_asset,
                           checkout_snipe_asset, USER_ARGS, CONFIG, clean_mac, clean_manufacturer, fill_macfields)
import xmltodict

# Stat file
try:
    report_stat = os.stat("report.xml")
except FileNotFoundError:
    report_stat = None

if not report_stat or (datetime.now().timestamp() - report_stat.st_mtime) > 86400:
    # Get report
    report1 = CONFIG['sccm']['report1']
    report2 = CONFIG['sccm']['report2']
    auth = HttpNtlmAuth(CONFIG['sccm']['username'], CONFIG['sccm']['password'])

    f1 = open("report.xml", 'wb')
    r1 = requests.get(report1, auth=auth)
    for chunk in r1.iter_content(chunk_size=512 * 1024):
        if chunk:  # filter out keep-alive new chunks
            f1.write(chunk)
    f1.close()
    # Get XML from response

    f2 = open("report2.xml", 'wb')
    r2 = requests.get(report2, auth=auth)
    for chunk in r2.iter_content(chunk_size=512 * 1024):
        if chunk:  # filter out keep-alive new chunks
            f2.write(chunk)
    f2.close()


def validate_ip(ip):
    # Validate this is an IPv4 address
    try:
        ip = ip.split(".")
        if len(ip) != 4:
            return None
        for octet in ip:
            octet = int(octet)
            if octet < 1 or octet > 254:
                return None
    except ValueError:
        return None

    # Check if this is a bogus IP address
    if int(ip[0]) in [127, 255]:
        return None
    if int(ip[0]) == 169 and int(ip[1]) == 254:
        return None
    if int(ip[0]) in range(224, 239):
        return None

    return ".".join(ip)


# Open XML file
tree = ElementTree.parse("report.xml")
with open('report2.xml') as fd:
    network_doc = xmltodict.parse(fd.read())

NETWORK_INFO = network_doc['feed']['entry']


def find_network_info(name) -> dict[str]:
    device_info = {}
    for xmlentry in NETWORK_INFO:
        this_computer = xmlentry['content']['m:properties']['d:Details_Table0_ComputerName']
        if this_computer.upper() == name.upper():
            ip = validate_ip(xmlentry['content']['m:properties']['d:IP_Address'])
            mac = clean_mac(xmlentry['content']['m:properties']['d:MAC_Address'])
            if ip and mac:
                device_info[mac] = ip
    return device_info


namespaces = {'m': 'http://schemas.microsoft.com/ado/2007/08/dataservices/metadata',
              'd': 'http://schemas.microsoft.com/ado/2007/08/dataservices',
              'atom': 'http://www.w3.org/2005/Atom'}
starts_with = "CVMAPDCEPIC01"
# For each entry tag
for entry in tree.findall('atom:entry', namespaces):
    # Get the content tag
    content = entry.find('atom:content', namespaces)
    updated = entry.find('atom:updated', namespaces).text
    # Parse 2023-10-07T13:21:09Z into datetime
    updated = datetime.strptime(updated, "%Y-%m-%dT%H:%M:%SZ")

    properties = content.find('m:properties', namespaces)
    # Example
    # <content device_type="application/xml">
    # 	<m:properties>
    # 		<d:CollectionID>UOR00B7C</d:CollectionID>
    # 		<d:Details_Table0_ResourceID m:device_type="Edm.Int32">16897059</d:Details_Table0_ResourceID>
    # 		<d:Details_Table0_ComputerName>ABCD123</d:Details_Table0_ComputerName>
    # 		<d:Details_Table0_DomainWorkgroup>DOMAIN</d:Details_Table0_DomainWorkgroup>
    # 		<d:Details_Table0_OU>domain/ou/ou/ou</d:Details_Table0_OU>
    # 		<d:Details_Table0_SMSSiteName>SMS Site Name</d:Details_Table0_SMSSiteName>
    # 		<d:Details_Table0_TopConsoleUser>Unknown</d:Details_Table0_TopConsoleUser>
    # 		<d:Details_Table0_OperatingSystem>Microsoft Windows 10 Enterprise</d:Details_Table0_OperatingSystem>
    # 		<d:Details_Table0_ServicePackLevel m:null="true" />
    # 		<d:Details_Table0_SerialNumber>SSS123S</d:Details_Table0_SerialNumber>
    # 		<d:Details_Table0_AssetTag></d:Details_Table0_AssetTag>
    # 		<d:Details_Table0_Manufacturer>Dell Inc.</d:Details_Table0_Manufacturer>
    # 		<d:Details_Table0_Model>Latitude 3450</d:Details_Table0_Model>
    # 		<d:Details_Table0_BIOS>A06</d:Details_Table0_BIOS>
    # 		<d:Details_Table0_MemoryKBytes m:device_type="Edm.Int64">8294148</d:Details_Table0_MemoryKBytes>
    # 		<d:Processor_Name>Intel(R) Core(TM) i5-5300U CPU @ 2.30GHz</d:Processor_Name>
    # 		<d:Details_Table0_ProcessorGHz m:device_type="Edm.Int32">2300</d:Details_Table0_ProcessorGHz>
    # 		<d:Processor_Max_Clock_Speed m:device_type="Edm.Int32">2301</d:Processor_Max_Clock_Speed>
    # 		<d:Details_Table0_DiskSpaceMB m:device_type="Edm.Int64">237302</d:Details_Table0_DiskSpaceMB>
    # 		<d:Details_Table0_FreeDiskSpaceMB m:device_type="Edm.Int64">156451</d:Details_Table0_FreeDiskSpaceMB>
    # 	</m:properties>
    # </content>
    # Get Details_Table0_ResourceID
    # Get Details_Table0_SerialNumber
    serial_number = clean_tag(properties.find('d:Details_Table0_SerialNumber', namespaces).text)
    resourceid = properties.find('d:Details_Table0_ResourceID', namespaces).text
    # Get Details_Table0_ComputerName
    computer_name = properties.find('d:Details_Table0_ComputerName', namespaces).text.upper()
    if starts_with and computer_name != starts_with:
        continue
    starts_with = None
    # Get Details_Table0_Domain
    domain = properties.find(
        'd:Details_Table0_DomainWorkgroup', namespaces).text
    # Get Details_Table0_OU, strip off the hostname
    ou_raw = properties.find('d:Details_Table0_OU', namespaces).text

    ou = ""
    if ou_raw:
        ou_parts = ou_raw.split("/")
        ou = "/".join(ou_parts[0:-1])
    # Get Details_Table0_TopConsoleUser
    top_console_user = properties.find(
        'd:Details_Table0_TopConsoleUser', namespaces).text
    # Get Details_Table0_OperatingSystem
    operating_system = properties.find(
        'd:Details_Table0_OperatingSystem', namespaces).text.replace("Microsoft ", "")
    # Get Details_Table0_ServicePackLevel
    service_pack_level = properties.find(
        'd:Details_Table0_ServicePackLevel', namespaces).text

    # Get Details_Table0_AssetTag
    asset_tag = clean_tag(properties.find('d:Details_Table0_AssetTag', namespaces).text)
    # Get Details_Table0_Manufacturer
    manufacturer = clean_manufacturer(properties.find('d:Details_Table0_Manufacturer', namespaces).text)
    # Get Details_Table0_Model
    model = clean_tag(properties.find('d:Details_Table0_Model', namespaces).text)

    memory = properties.find('d:Details_Table0_MemoryKBytes', namespaces).text or 0
    # Get Processor_Name
    processor_name = properties.find('d:Processor_Name', namespaces).text
    # Get Details_Table0_DiskSpaceMB
    disk_space = properties.find('d:Details_Table0_DiskSpaceMB', namespaces).text

    if model:
        model = model.replace("Dell System ", "").replace("Dell ", "")

    if str(serial_number).lower() == str(model).lower():
        serial_number = ""

    if str(asset_tag).lower() == str(model).lower():
        asset_tag = ""

    model_id = get_snipe_model_id(model, manufacturer, "computer")
    payload = {"name": computer_name, "serial": serial_number, "model_id": model_id, "asset_tag": asset_tag,
               "status_id": 2, "category_id": 2, '_snipeit_ram_2': round(int(memory) / 1024),
               '_snipeit_operating_system_8': operating_system}

    # Custom fields
    if service_pack_level:
        payload['_snipeit_os_version_9'] = service_pack_level

    # Make sure domain is valid
    if domain and (domain.isalnum() or domain.replace("-", "").replace("_", "").isalnum()):
        payload['_snipeit_domain_11'] = domain

    if ou:
        payload['_snipeit_ou_12'] = ou
    if disk_space:
        payload['_snipeit_storage_3'] = disk_space
    if processor_name:
        payload['_snipeit_cpu_name_14'] = processor_name

    # Get network info
    mac_addresses = find_network_info(computer_name)
    if mac_addresses:
        mac_address = next(iter(mac_addresses))
        payload["_snipeit_ip_address_13"] = next(iter(mac_addresses.values()))
    else:
        mac_address = None

    if not asset_tag:
        logging.info(f"No asset tag for {computer_name}")
        payload['asset_tag'] = f"sccm-{resourceid}"

    snipe_asset = get_snipe_asset(serial=serial_number,
                                  mac_addresses=mac_addresses,
                                  name=computer_name,
                                  asset_tag=payload['asset_tag'])

    if not serial_number:
        logging.error(f"No serial number for {computer_name}")
        payload['serial'] = f"sccm-{resourceid}"

    if snipe_asset['total'] > 1:
        logging.error(f"Multiple assets found for {serial_number}")
        continue

    payload = fill_macfields(snipe_asset, payload, list(mac_addresses.keys()))

    if not snipe_asset['total']:
        asset = create_snipe_asset(payload)
    elif snipe_asset['total'] == 1:
        asset = snipe_asset['rows'][0]
        asset_id = asset['id']

        update_time = asset['updated_at']['datetime']
        # Convert to datetime object
        update_time = datetime.strptime(update_time, '%Y-%m-%d %H:%M:%S')
        if update_time >= updated and not USER_ARGS.force:
            logging.info(f"Skipping update for {asset['id']} because the Snipe record is newer.")
            continue

        if asset['serial'] == payload['serial'] or payload['serial'].startswith('sccm'):
            del payload['serial']
        if asset['asset_tag'] == payload['asset_tag'] or payload['asset_tag'].startswith('sccm'):
            del payload['asset_tag']
        if asset['name'] == payload['name']:
            del payload['name']
        if asset['model']['id'] == payload['model_id']:
            del payload['model_id']
        if asset['status_label']['id'] == payload['status_id']:
            del payload['status_id']
        if asset['category']['id'] == payload['category_id']:
            del payload['category_id']

        if asset['custom_fields']['IP Address']['field'] in payload and asset['custom_fields']['IP Address']['value']:
            del payload[asset['custom_fields']['IP Address']['field']]

        for key, value in asset['custom_fields'].items():
            if (value['field'] in payload and
                    str(payload[value['field']]).strip() == html.unescape(str(value['value'])).strip()):
                del payload[value['field']]

        # Update asset
        if payload:
            asset = update_snipe_asset(asset_id, payload)

    if (USER_ARGS.users or USER_ARGS.users_force) and top_console_user:
        checkout_snipe_asset(top_console_user, asset)
