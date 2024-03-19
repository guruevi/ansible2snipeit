#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from configparser import RawConfigParser
from csv import reader
from os import path, listdir
from shutil import move

from snipeit_api.api import SnipeITApi
from snipeit_api.helpers import clean_ip, clean_mac, clean_tag, validate_category, validate_os, \
    convert_to_bool, get_os_type
from snipeit_api.models import Hardware

logging.basicConfig(level=logging.INFO)
CONFIG = RawConfigParser()
logging.debug("Checking for a settings.conf ...")
CONFIG.read("settings.conf")
snipeit_apiurl = CONFIG.get('snipe-it', 'url')
snipeit_apikey = CONFIG.get('snipe-it', 'apikey')
api = SnipeITApi(snipeit_apiurl, snipeit_apikey)
INPUT_DIR = CONFIG.get('csv', 'input')
OUTPUT_DIR = CONFIG.get('csv', 'output')
# Read a line from CSV
# See if we have any files in the CSV_IN, loop through them
for file in listdir(f'{INPUT_DIR}'):
    if not file.endswith(".csv"):
        continue
    # Log to file
    logging.basicConfig(filename=path.join(OUTPUT_DIR, f'{file}.log'), level=logging.INFO, force=True)
    logging.info(f"Processing {file}")
    csv_fd = open(path.join(INPUT_DIR, file), 'r')
    csv_file = reader(csv_fd)
    # Skip the two headers
    next(csv_file)
    header = next(csv_file)
    # Parse the header
    if header[0] != "IP Address":
        logging.error(f"Invalid header {header[0]}, this does not seem like a valid file")
        continue

    for row in csv_file:
        # Strip each element
        row = [x.strip() for x in row]
        ip = clean_ip(row[0])
        # Make sure we don't get FQDN
        name = clean_tag(row[1].split('.')[0].strip().upper())
        # Skip if name is invalid
        if not name:
            logging.error(f"Invalid name: {row[1]}, skipping")
            continue
        owner = row[2].strip()
        category = validate_category(row[3].strip().split(' ')[0].lower())
        if not category:
            logging.error(f"Invalid category {row[3]}, skipping")
            continue
        operating_system = validate_os(row[4].strip())
        if not operating_system:
            logging.error(f"Invalid operating system for {name}: {row[4]}, OS will not be set")
        os_type = get_os_type(operating_system)
        os_version = row[5]
        serial = row[6].strip().upper()
        serial = clean_tag(serial)
        if not serial:
            logging.error(f"Invalid serial number for {name}: {row[6]}, serial will not be set")
        disk_encrypted = convert_to_bool(row[7])
        antivirus = convert_to_bool(row[8])  # we will be the judge of that
        # hardened = row[9] - we will be the judge of that
        # managed = row[10] - we will be the judge of that
        domain = row[11].upper()
        eol = convert_to_bool(row[12])
        department = row[15].strip()
        macaddresses = []
        for macaddress in row[13].split(','):
            macaddress = clean_mac(macaddress)
            if not macaddress:
                continue
            macaddresses.append(macaddress)
        asset_tag = row[14].strip().upper()

        if not serial and not macaddresses:
            logging.error(f"Serial number nor MAC address found for {name}. Cannot uniquely identify asset.")
            continue
        # Check Snipe-IT for the asset
        asset = (Hardware(api=api,
                          name=name,
                          serial=serial,
                          notes=f"Imported by CSV - {owner}"
                          )
                 .set_custom_field("Domain", domain)
                 .set_custom_field("Operating System", operating_system)
                 .set_custom_field("OS Version", os_version)
                 .set_custom_field("OS Type", os_type)
                 .set_custom_field("IP Address", ip)
                 .get_by_mac(macaddresses)
                 .get_by_serial()
                 .set_custom_field("Department", department)
                 )
        # If we have a valid asset, we rely on the database to tell us the details
        status_id = 4
        if not asset.get_custom_field("EDR") or not asset.get_custom_field("Domain") or not disk_encrypted or eol:
            status_id = 5
        asset.populate({'status_id': status_id}).upsert()

    csv_fd.close()
    # Move the file to the output directory
    move(path.join(INPUT_DIR, file), path.join(OUTPUT_DIR, file))
