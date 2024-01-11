#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This will get a list of systems from an ordered CSV and put them into Snipe-IT as "need-to-audit" assets.

import csv
import os
import logging
import shutil

from ansible2snipe import (CONFIG, clean_manufacturer, clean_tag, get_snipe_model_id, get_snipe_asset,
                           update_snipe_asset, create_snipe_asset, clean_mac, validate_ip, fill_macfields)


def validate_os(operating_system: str) -> str | None:
    # Check if the OS is in the list of valid OSes
    valid_os = ["AlmaLinux", "Android", "Android 6", "Android 7", "APC AOS", "Axis OS", "BSD", "CentOS",
                "C Executive OS", "ChromeOS 13020.97", "Cisco IOS", "Cisco IOS Software",
                "Cisco IOS Software [Bengaluru]", "Cisco IOS Software [Cupertino]", "Cisco IOS Software [Denali]",
                "Cisco IOS Software [Dublin]", "Cisco IOS Software [Everest]", "Cisco IOS Software [Fuji]",
                "Cisco IOS Software [Gibraltar]", "Cisco IOS XE", "Cisco NX-OS", "CoBos", "CollabOS", "Debian", "DSM",
                "Embedded Linux", "Embedded Windows 7", "ENEA OSE 4.5.2", "Evolution OS", "Fedora", "Fire OS",
                "FortiOS", "FreeBSD", "HELiOS", "HP FutureSmart", "HP ProCurve", "iOS", "IOS XE", "JunOS", "Link-OS",
                "Linux", "Linux Embedded OS", "Linux Embedded RTOS", "Linux Yocto", "macOS", "Mac OS X", "Meraki OS",
                "OpenVMS", "OS X", "PAN-OS", "Pump OS", "QNX RTOS", "QTS", "RedHat", "RHEL 7.9", "Ricoh-OS", "RokuOS",
                "SonicOS", "SRS", "SUSE", "TC7", "Telium2", "Tizen", "Total Access 924e (2nd Gen),", "tvOS", "Ubuntu",
                "Uniform-OS", "VxWorks", "watchOS", "webOS", "Windows", "Windows 7", "Windows 7 Enterprise",
                "Windows 7 Professional", "Windows 7 Ultimate", "Windows 8", "Windows 8.1", "Windows 8.1 Pro",
                "Windows 10", "Windows 10 Education", "Windows 10 Enterprise", "Windows 10 Enterprise 2015 LTSB",
                "Windows 10 Enterprise 2016 LTSB", "Windows 10 Enterprise LTSC", "Windows 10 Enterprise N",
                "Windows 10 IoT Enterprise", "Windows 10 IoT Enterprise LTSC", "Windows 10 Pro",
                "Windows 10 Pro for Workstations", "Windows 11", "Windows 11 Enterprise",
                "Windows 11 Enterprise multi-session", "Windows 11 Enterprise N", "Windows 11 Pro",
                "Windows 11 Pro for Workstations", "Windows 2000", "Windows CE", "Windows Embedded Standard",
                "Windows Server 2008", "Windows Server 2008 R2 Standard", "Windows Server 2012 R2",
                "Windows Server 2012 R2 Datacenter", "Windows Server 2012 R2 Standard", "Windows Server 2012 Standard",
                "Windows Server 2016", "Windows Server 2016 Datacenter", "Windows Server 2016 Standard",
                "Windows Server 2019", "Windows Server 2019 Datacenter", "Windows Server 2019 Standard",
                "Windows Server 2022", "Windows Server 2022 Datacenter", "Windows Server 2022 Standard",
                "Windows Storage Server 2012 R2 Standard", "Windows Storage Server 2012 R2 Workgroup",
                "Windows Storage Server 2016 Standard", "Windows Storage Server 2016 Workgroup", "Windows XP",
                "Windows XP 64bit", "Windows XP Professional"]

    if operating_system in valid_os:
        return operating_system

    return None


INPUT_DIR = CONFIG['csv']['input']
OUTPUT_DIR = CONFIG['csv']['output']
# Read a line from CSV
# See if we have any files in the CSV_IN, loop through them
for file in os.listdir(f'{INPUT_DIR}'):
    if file.endswith(".csv"):
        # Log to file
        logging.basicConfig(filename=os.path.join(OUTPUT_DIR, f'{file}.log'), level=logging.INFO, force=True)
        logging.info(f"Processing {file}")
        with open(os.path.join(INPUT_DIR, file), 'r') as csvfile:
            reader = csv.reader(csvfile)
            # Skip the header
            next(reader)
            next(reader)
            for row in reader:
                ip = validate_ip(row[0].strip())
                name = row[1].split('.')[0].strip().upper().replace(' ', '-')
                owner = row[2].strip()
                category = row[3].strip().split(' ')[0].lower()
                # Strip off any s on the end of the category
                if category.endswith('s'):
                    category = category[:-1]
                operating_system = validate_os(row[4].strip())
                # os_version = row[5]
                serial = row[6].strip().upper()
                # disk_encrypted = row[7]
                # antivirus = row[8]
                # hardened = row[9]
                # managed = row[10]
                # domain = row[11]
                # eol = row[12]
                macaddresses = []
                for macaddress in row[13].split(','):
                    macaddress = clean_mac(macaddress)
                    if not macaddress:
                        continue
                    macaddresses.append(macaddress)
                asset_tag = row[14].strip().upper()

                if not serial and not macaddresses and not asset_tag:
                    logging.error(f"Serial number, MAC address or Asset Tag not found for {name}.")
                    continue
                # Check Snipe-IT for the asset
                snipe_asset = get_snipe_asset(serial=serial, name=name, mac_addresses=macaddresses, asset_tag=asset_tag)

                # If we have more than one asset, log an error and skip
                if snipe_asset['total'] > 1:
                    logging.error(f"Multiple assets in Snipe-IT for {name}, {serial}, {macaddress} or {asset_tag} - "
                                  "clean up Snipe-IT and try again.")
                    continue

                if snipe_asset['total'] == 1:
                    logging.info(f"Existing Asset found in Snipe-IT for {name}, {serial}, {macaddress} or {asset_tag} ")
                    # Update the asset if asset tag is passed
                    payload = {}
                    if asset_tag:
                        payload["asset_tag"] = asset_tag
                    if serial:
                        payload["serial"] = serial
                    if name:
                        payload["name"] = name
                    if ip:
                        payload["_snipeit_ip_address_13"] = ip
                    if macaddresses:
                        payload = fill_macfields(snipe_asset, payload, macaddresses)
                    if operating_system:
                        payload["_snipeit_operating_system_8"] = operating_system
                    # Check if status is set to "Unmanaged (Research)"
                    if snipe_asset['rows'][0]['status_label']['id'] == 1:
                        payload['status_id'] = 4

                    payload['notes'] = f"Imported from {file}. {owner} is the owner."
                    update_snipe_asset(snipe_asset['rows'][0]['id'], payload)
                    continue

                # If we have no assets, create one
                logging.info(f"Creating a new asset in Snipe-IT for {name}, set it to 'Unmanaged (Research)'")
                if not asset_tag:
                    asset_tag = f"csv-{name.replace(' ', '_')}"

                payload = {'name': name, 'serial': serial, 'status_id': 4,
                           'category_id': CONFIG.get('snipe-it', f'{category}_category', fallback=2),
                           '_snipeit_operating_system_8': os, 'asset_tag': asset_tag, 'model_id': 11,
                           'notes': f"Imported from {file}. {owner} is the owner."}

                if ip:
                    payload["_snipeit_ip_address_13"] = ip

                number = len(macaddresses)
                if number == 1:
                    payload['_snipeit_mac_address_1'] = macaddresses[0]
                if number > 1:
                    payload['_snipeit_mac_address_2_5'] = macaddresses[1]
                if number > 2:
                    payload['_snipeit_mac_address_3_6'] = macaddresses[2]
                if number > 3:
                    payload['_snipeit_mac_address_4_7'] = macaddresses[3]

                create_snipe_asset(payload)
        # Move the file to the output directory
        shutil.move(os.path.join(INPUT_DIR, file), os.path.join(OUTPUT_DIR, file))
