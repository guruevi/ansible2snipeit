#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy
import logging
from configparser import RawConfigParser
from csv import reader
from io import StringIO
from os import path, listdir
from shutil import move

import openpyxl
import xlrd

from snipeit_api.api import SnipeITApi
from snipeit_api.defaults import DEFAULTS
from snipeit_api.helpers import clean_ip, clean_mac, clean_tag, validate_os, get_os_type, validate_hostname
from snipeit_api.models import Hardware

logging.basicConfig(level=logging.DEBUG)
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

def read_xls(file_path: str) -> list:
    output = []
    sheet = xlrd.open_workbook(file_path).sheet_by_index(0)
    for nrow in range(sheet.nrows):
        output[nrow] = []
        for ncol in range(sheet.ncols):
            output[nrow][ncol] = sheet.cell_value(nrow, ncol)
    return output


def read_csv(file_path: str) -> list:
    output = []
    with open(file_path, 'r') as csv_fd:
        csv_file = reader(csv_fd)
        for line in csv_file:
            output.append(line)
    return output


def read_xlsx(file_path: str) -> list:
    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active
    output = []
    for line in sheet.iter_rows(values_only=True):
        output.append(list(line))
    return output


def csv2snipe(file: str) -> str:
    log_stream = StringIO()
    logging.basicConfig(stream=log_stream, level=logging.INFO, force=True)
    logging.info(f"Processing {file}")
    if file.endswith(".xls"):
        lines = read_xls(file)
    elif file.endswith(".csv"):
        lines = read_csv(file)
    elif file.endswith(".xlsx"):
        lines = read_xlsx(file)
    else:
        logging.error(f"Invalid file type: {file}, skipping")
        return log_stream.getvalue()
    logging.debug(lines)
    # Asset Name    Asset Tag	Serial	Category	MAC Address 1	IP Address	Domain	Department	Last User
    # 0             1           2       3           4               5           6       7           8
    # Operating System	CPU	Internet	EDR	Management	Org. Unit	Lab
    # 9                 10  11          12  13          14          15

    # Check the header
    valid_header = ["Asset Name", "Asset Tag", "Serial", "Category", "MAC Address 1", "IP Address", "Domain",
                    "Department", "Last User", "Operating System", "CPU", "Internet", "EDR", "Management", "Org. Unit",
                    "Lab"]
    if lines[0][0:len(valid_header)] != valid_header:
        logging.error(f"Invalid header: {lines[0:len(valid_header)]}, this does not seem like a valid inventory file")
        logging.error(f"Valid header: {valid_header}")
        return log_stream.getvalue()

    for row_raw in lines[1:]:
        # Skip if all fields are None
        if not any(row_raw):
            continue
        logging.debug(f"Processing {row_raw}")
        asset_tag = clean_tag(row_raw[1])
        # Strip each field and convert None to ''
        row = [clean_tag(str(field).strip()) if field else '' for field in row_raw]
        ip = clean_ip(row[5])
        # Make sure we don't get FQDN
        name = validate_hostname(row[0].strip())
        # Skip if name is invalid
        if not name:
            logging.error(f"Invalid name: {row[0]}, skipping record")
            continue
        lab = row[15].title()
        operating_system = validate_os(row[9])
        if not operating_system:
            logging.error(f"Invalid operating system for {name}: {row[9]}, OS will not be set")
            logging.info("Valid operating systems: " + ', '.join(DEFAULTS['valid_os']))
        os_type = get_os_type(operating_system)
        serial = row[2].upper()
        macaddresses = []
        for macaddress in row[4].split(','):
            macaddress = clean_mac(macaddress)
            if not macaddress:
                continue
            macaddresses.append(macaddress)
        department = row[7].strip()
        # Test if there are any non-alphanumeric characters except -
        if not serial.replace('-', '').isalnum():
            serial = ''
        if not serial and not macaddresses:
            logging.error(f"No (valid) serial number or MAC address found for {name}. Cannot uniquely identify asset.")
            continue
        if not serial:
            serial = macaddresses[0].replace(':', '').upper()
        if not asset_tag:
            asset_tag = f"IMPORT-{serial}"
        try:
            # Check Snipe-IT for the asset
            asset = (Hardware(api=api,
                              name=name,
                              serial=serial,
                              asset_tag=asset_tag,
                              model_id=DEFAULTS['model_id'],
                              notes=f"Imported by CSV",
                              custom_fields=copy.deepcopy(DEFAULTS['custom_fields']),
                              status_id=DEFAULTS['status_id_pending']
                              )
                     .set_custom_field("Operating System", operating_system)
                     .set_custom_field("OS Type", os_type)
                     .set_custom_field("IP Address", ip)
                     .get_by_serial()
                     .get_by_mac(macaddresses)
                     .get_by_name()
                     .store_state()
                     .set_custom_field("Department", department)
                     .set_custom_field("Lab", lab)
                     .populate_mac(macaddresses)
                     )
            # If we have a valid asset, we rely on the database to tell us the details
            if asset.status_id == DEFAULTS['status_id_pending'] or asset.status_id == 5:
                status_id = 5
            else:
                status_id = 4
            setattr(asset, 'status_id', status_id)
            asset.upsert()
        except ValueError as e:
            logging.error(f"An error occurred while processing {row}: {e}")

    return log_stream.getvalue()


def main():
    errors = ''
    for file in listdir(INPUT_DIR):
        if file.endswith(".xls") or file.endswith(".csv") or file.endswith(".xlsx"):
            full_path = path.join(INPUT_DIR, file)
            errors += csv2snipe(full_path)
            if errors:
                logging.error(f"Errors occurred while processing {file}")
                logging.debug(errors)
                move(path.join(INPUT_DIR, file), path.join(OUTPUT_DIR, file))
            else:
                logging.info(f"Processed {file} successfully")
                move(path.join(INPUT_DIR, file), path.join(OUTPUT_DIR, file))
    # Write log to disk
    with open(path.join(OUTPUT_DIR, 'import.log'), 'a') as log_fd:
        log_fd.write(errors)


if __name__ == '__main__':
    main()
