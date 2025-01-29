#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This will get a list of systems from ORDR and put them into Snipe-IT as "need-to-audit" assets.
import ipaddress
import os

from requests import get
from requests.auth import HTTPBasicAuth
import logging
from configparser import RawConfigParser
from snipeit_api.helpers import clean_manufacturer, clean_mac, clean_tag, clean_os

CONFIG = RawConfigParser()
logging.debug("Checking for a settings.conf ...")
CONFIG.read("settings.conf")
# Get the ORDR API key from CONFIG
ordr_username = CONFIG.get('ordr', 'username')
ordr_password = CONFIG.get('ordr', 'password')
ordr_url = CONFIG.get('ordr', 'url')
ordr_tls_verify = CONFIG.getboolean('ordr', 'tls_verify')

# Basic Auth
auth = HTTPBasicAuth(ordr_username, ordr_password)

next_page = "/Rest/Devices"
# Get the first page from a save place
# try:
#     with open('last_page.txt', 'r') as the_file:
#         next_page = the_file.read()
# except FileNotFoundError:
#     pass

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
    next_page = f"{next_page}?{parameter}={value}"

while next_page:
    # Get the first page of results
    response = get(ordr_url + next_page, auth=auth, verify=ordr_tls_verify)
    # logging.debug(response.text)
    data = response.json()

    if 'MetaData' in data and 'next' in data['MetaData'] and data['MetaData']['next']:
        # Write next_page to disk in case we crash
        # with open('last_page.txt', 'w') as the_file:
        #     the_file.write(next_page)
        next_page = data['MetaData']['next']
    else:
        # Delete last_page.txt if we are at the end of our roll
        # try:
        #     os.remove('last_page.txt')
        # except FileNotFoundError:
        #     pass
        next_page = None

    if 'Devices' not in data:
        if 'MacAddress' in data:
            logging.info("Single device filtered")
            data['Devices'] = [data]

    for device in data['Devices']:
        logging.info(f"Processing {device['deviceName']}")
        # logging.debug(device)

        # DHCP hostname is reported by the device, deviceName is reported by the DNS server
        if 'dhcpHostname' in device:
            name = device['dhcpHostname'].split('.')[0].upper()
        else:
            name = device['deviceName'].split('.')[0].upper()

        macaddress = clean_mac(device['MacAddress'])
        if not macaddress:
            logging.warning(f"WARNING: Invalid MAC address {device['MacAddress']} found for {name}. Skipping.")
            continue

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
            serial = clean_tag(device['SerialNo'].upper())
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
            logging.error(f"WARNING: Category {device['Group']} not found. Skipping.")
            continue

        # ORDR has a lot of duplicate names, but should match on serial and MAC addresses
        snipe_asset = get_snipe_asset(serial=serial, mac_addresses=[macaddress])

        # logging.debug(snipe_asset)
        if snipe_asset['total'] > 1:
            logging.error(f"Multiple assets in Snipe-IT for {name}, {serial}, {macaddress}")
            continue

        model_id = get_snipe_model_id(model, manufacturer, device_type)
        # Create a payload:
        if not serial:
            logging.debug(f"WARNING: Serial number not found for {name}.")
            serial = "ORDR-" + macaddress.replace(':', '').upper()

        payload = {
            "serial": serial,
            "model_id": model_id,
            "_snipeit_vlan_17": vlan,
            "_snipeit_vlan_name_18": vlanname
        }

        try:
            payload['_snipeit_ip_address_13'] = str(ipaddress.ip_address(device['IpAddress']))
        except (ValueError, KeyError):
            print(f"Error: {name} no correct IP address.")

        if 'nwEquipHostname' in device:
            payload["_snipeit_switch_15"] = device['nwEquipHostname']

        if 'nwEquipInterface' in device:
            payload['_snipeit_switch_port_16'] = device['nwEquipInterface']

        # The OU is comma separated, so we need to reverse it and use / as a separator
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

        asset = {}

        if snipe_asset['total'] == 0:
            logging.info(f"Creating a new asset in snipe for {name}")
            payload['status_id'] = 1
            payload['name'] = name
            payload['category_id'] = CONFIG.get('snipe-it', f'{device_type}_category'),

            # logging.debug(payload)
            if macaddress:
                payload['asset_tag'] = "ORDR-" + macaddress.replace(':', '_').upper()
            else:
                payload['asset_tag'] = "ORDR-" + name.upper()
            if 'OsType' in device and device['OsType']:
                payload['_snipeit_operating_system_8'] = clean_os(device['OsType'])
            if 'OsVersion' in device and device['OsVersion']:
                os_version = device['OsVersion']
                payload['_snipeit_os_version_9'] = os_version
            payload = fill_macfields(asset, payload, [macaddress])
            asset = create_snipe_asset(payload)
        elif snipe_asset['total'] == 1:
            logging.info(f"Existing asset in Snipe-IT for {name}")
            asset = snipe_asset['rows'][0]
            if not asset or 'id' not in asset:
                logging.error(f"Asset not found for {name}")
                continue
            payload = fill_macfields(asset, payload, [macaddress])
            if payload['serial'].startswith('ORDR-'):
                del payload['serial']

            # ORDR is less accurate on these things
            try:
                if not asset['custom_fields']['Operating System']['value'] and 'OsType' in device and device['OsType']:
                    payload['_snipeit_operating_system_8'] = clean_os(device['OsType'])

                if not asset['custom_fields']['OS Version']['value'] and 'OsVersion' in device and device['OsVersion']:
                    payload['_snipeit_os_version_9'] = device['OsVersion']

                if '_snipeit_ou_12' in payload and asset['custom_fields']['OU']['value']:
                    del payload['_snipeit_ou_12']

                if '_snipeit_domain_11' in payload and asset['custom_fields']['Domain']['value']:
                    del payload['_snipeit_domain_11']
            except (KeyError, ValueError):
                logging.error(f"Error: {name} has incorrect custom fields.")

            if payload['model_id'] == 11 or asset['model']['id'] != 11:
                del payload['model_id']

            if payload:
                ret = update_snipe_asset(asset, payload)

            logging.debug(f"Done updating {name}")
