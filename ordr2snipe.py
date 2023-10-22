#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This will get a list of systems from ORDR and put them into Snipe-IT as "need-to-audit" assets.

import html
import os

from requests import get
from requests.auth import HTTPBasicAuth
import logging
from ansible2snipe import (CONFIG, clean_manufacturer, clean_tag, get_snipe_model_id, get_snipe_asset,
                           update_snipe_asset, create_snipe_asset, clean_mac, clean_os)

# Get the ORDR API key from CONFIG
ordr_username = CONFIG.get('ordr', 'username')
ordr_password = CONFIG.get('ordr', 'password')
ordr_url = CONFIG.get('ordr', 'url')
ordr_tls_verify = CONFIG.getboolean('ordr', 'tls_verify')

# Basic Auth
auth = HTTPBasicAuth(ordr_username, ordr_password)

# Get the first page from a save place
try:
    with open('last_page.txt', 'r') as the_file:
        next_page = the_file.read()
except FileNotFoundError:
    next_page = "/Rest/Devices"

# Get environment variables
valid_params = ["os-type", "connStatus", "filter-by-ext-data", "type", "mac", "iot", "weakPassword", "attribute-filter",
                "include-ext-data", "limit", "model", "startTime", "vulnIds", "endpointToken", "include-ext-data-ref",
                "riskState", "group", "include", "sensorName", "appName", "ip", "profile", "tenantGuid", "version",
                "userId", "biosPassword", "mfg", "filter", "mfg-long", "os-version", "patchInstalled", "serial",
                "has-flow-vectors", "policy-profile", "sw-version", "location", "diskEncrypted", "endTime", "sensorIp",
                "clientMacToken", "subcategory", "softwareInstalled", "openPorts"]
parameter = os.getenv('ORDR_PARAM', None)
value = os.getenv('ORDR_VALUE', None)
query_param = ""

if parameter in valid_params:
    query_param = f"?{parameter}={value}"

while next_page:
    # Get the first page of results
    response = get(ordr_url + next_page + query_param, auth=auth, verify=ordr_tls_verify)
    data = response.json()

    if 'MetaData' in data and 'next' in data['MetaData'] and data['MetaData']['next']:
        # Write next_page to disk in case we crash
        with open('last_page.txt', 'w') as the_file:
            the_file.write(next_page)

        next_page = data['MetaData']['next']
    else:
        next_page = None

    if 'Devices' not in data:
        if 'MacAddress' in data:
            logging.info("Single device filtered")
            data['Devices'] = [data]

    for device in data['Devices']:
        logging.info(f"Processing {device['deviceName']}")
        logging.debug(device)

        # DHCP hostname is reported by the device, deviceName is reported by the DNS server
        if 'dhcpHostname' in device:
            name = device['dhcpHostname'].split('.')[0].upper()
        else:
            name = device['deviceName'].split('.')[0].upper()
        macaddress = clean_mac(device['MacAddress'])

        if 'MfgName' in device:
            manufacturer = clean_manufacturer(clean_tag(device['MfgName']))
        else:
            manufacturer = "Unknown"

        if 'ModelNameNo' in device and device['ModelNameNo']:
            model = device['ModelNameNo']
        else:
            model = 'Unknown'

        vlan = device['Vlan']
        vlanname = device['vlanName']

        if 'SerialNo' in device:
            serial = clean_tag(device['SerialNo'])
        else:
            serial = None

        if device['Group'] == "Workstations" or device['Group'] == "Servers":
            device_type = "computer"
        elif device['Group'].startswith("Medical "):
            device_type = "medical"
        elif device['Group'].startswith("Network "):
            device_type = "network"
        elif device['Group'] in ("Mobile Devices", "Mobile Phones and Tablets"):
            device_type = "mobile"
        elif device['Group'] == "Embedded Devices" or device['Group'] == "Thin Clients":
            device_type = "embedded"
        elif device['Group'] == "Life Science Devices":
            device_type = "research"
        elif device['Group'] == "Printers and Copiers":
            device_type = "printer"
        elif device['Group'] == "Facility Devices" or device['Group'] == "Physical Security Devices":
            device_type = "facility"
        elif device['Group'] == "Others":
            device_type = "other"
        elif device['Group'] == "Storage Devices" or device['Group'] == "Media Devices":
            device_type = "storage"
        elif device['Group'] == "Industrial Devices":
            device_type = "industrial"
        elif device['Group'] == "IP Phones":
            device_type = "phone"
        elif device['Group'] == "Retail Devices":
            device_type = "pos"
        elif device['Group'] == "Shadow IoT":
            device_type = "iot"
        elif device['Group'] == "Gaming Devices":
            device_type = "gaming"
        else:
            print(f"WARNING: Category {device['Group']} not found. Skipping.")
            continue

        if macaddress:
            asset_tag = "ordr-" + macaddress.replace(':', '_')
        else:
            asset_tag = "ordr-" + name

        snipe_asset = get_snipe_asset(serial=serial, mac_address=macaddress, name=name, asset_tag=asset_tag)

        if snipe_asset['total'] > 1:
            logging.error(f"Multiple assets in Snipe-IT for {name}")
            logging.debug(snipe_asset)
            continue

        model_id = get_snipe_model_id(model, manufacturer, device_type)
        # Create a payload:
        if not serial:
            print(f"WARNING: Serial number not found for {name}.")
            serial = f"ordr-{macaddress.replace(':', '')}"

        payload = {
            "name": name,
            "serial": serial,
            "status_id": 1,
            "category_id": CONFIG.get('snipe-it', f'{device_type}_category'),
            "model_id": model_id,
            "asset_tag": asset_tag,
            "_snipeit_vlan_17": vlan,
            "_snipeit_vlan_name_18": vlanname,
            "_snipeit_mac_address_1": device['MacAddress']
        }

        if 'IpAddress' in device:
            payload["_snipeit_ip_address_13"] = device['IpAddress']

        if 'nwEquipHostname' in device:
            payload["_snipeit_switch_15"] = device['nwEquipHostname']

        if 'nwEquipInterface' in device:
            payload['_snipeit_switch_port_16'] = device['nwEquipInterface']

        # Reverse Computers,Psychiatry,Departmental OUs,URMC into URMC/Departmental OUs/Psychiatry/Computers
        if 'ou' in device:
            # Get domain from FQDN
            fqdn_split = device['fqdn'].split('.')
            domain = fqdn_split[1].upper()
            dns_domain = ".".join(fqdn_split[1:]).lower()
            ou_split = device['ou'].split(',')
            ou_split.reverse()
            ou = f"{dns_domain}/" + '/'.join(ou_split)
            payload['_snipeit_domain_11'] = domain
            payload['_snipeit_ou_12'] = ou

        if 'OsType' in device and device['OsType']:
            payload['_snipeit_operating_system_8'] = clean_os(device['OsType'])
        if 'OsVersion' in device and device['OsVersion']:
            os_version = device['OsVersion']
            payload['_snipeit_os_version_9'] = os_version

        asset = {}
        if snipe_asset['total'] == 0:
            logging.info(f"Creating a new asset in snipe for {name}")
            logging.debug(payload)
            asset = create_snipe_asset(payload)

        if snipe_asset['total'] == 1:
            logging.info(f"Existing asset in Snipe-IT for {name}")
            asset = snipe_asset['rows'][0]

            if (payload['serial'] == asset['serial'] or
                    payload['serial'].startswith('ordr-') or
                    not asset['serial'].startswith('ordr-')):
                del payload['serial']

            # ORDR is less accurate on these things
            if name == macaddress or asset['name'] != macaddress:
                del payload['name']
            del payload['asset_tag']
            del payload['model_id']
            del payload['status_id']
            del payload['category_id']

            snipe_macaddress = []
            snipe_macaddress_field = []
            for key, value in asset['custom_fields'].items():
                if value['field_format'] == 'MAC':
                    if value['value']:
                        snipe_macaddress.append(value['value'])
                    snipe_macaddress_field.append(value['field'])

                if value['field'] in payload and value['value']:
                    del payload[value['field']]

            if macaddress and macaddress not in snipe_macaddress:
                payload[snipe_macaddress_field[len(snipe_macaddress) + 1]] = macaddress

            for key in asset:
                if key in payload and html.unescape(str(asset[key])) == str(payload[key]):
                    del payload[key]

            if payload:
                ret = update_snipe_asset(asset['id'], payload)

            logging.debug(f"Done updating {name}")