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
from snipeit_api.helpers import clean_ip, clean_mac, clean_tag, validate_category, validate_os, get_os_type, \
    validate_hostname, send_email
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
        row_number = 0
        for line in csv_file:
            output[row_number] = line
            row_number += 1
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
    logging.debug(f"Processing {file}")
    if file.endswith(".xls"):
        lines = read_xls(file)
    elif file.endswith(".csv"):
        lines = read_csv(file)
    elif file.endswith(".xlsx"):
        lines = read_xlsx(file)
    else:
        logging.error(f"Invalid file type: {file}, skipping")
        return log_stream.getvalue()

    # Skip the header
    if lines[0][0] != "IP Address":
        logging.error(f"Invalid header: {lines[0]}, this does not seem like a valid inventory file")
        return log_stream.getvalue()

    for row_raw in lines:
        if row_raw[0] == "IP Address":
            continue
        # Skip if all fields are None
        if not any(row_raw):
            continue
        logging.debug(f"Processing {row_raw}")
        # Strip each field and convert None to ''
        row = [clean_tag(str(field).strip()) if field else '' for field in row_raw]
        ip = clean_ip(row[0])
        # Make sure we don't get FQDN
        name = validate_hostname(row[1].strip())
        # Skip if name is invalid
        if not name:
            logging.error(f"Invalid name: {row[1]}, skipping record")
            continue
        owner = row[2].title()
        lab = row[3].title()
        location = row[4].title()
        category = validate_category(row[5])
        operating_system = validate_os(row[6])
        if not operating_system:
            logging.error(f"Invalid operating system for {name}: {row[6]}, OS will not be set")
            logging.info("Valid operating systems: " + ', '.join(DEFAULTS['valid_os']))
        os_type = get_os_type(operating_system)
        serial = row[7].upper()
        macaddresses = []
        for macaddress in row[8].split(','):
            macaddress = clean_mac(macaddress)
            if not macaddress:
                continue
            macaddresses.append(macaddress)
        for macaddress in row[9].split(','):
            macaddress = clean_mac(macaddress)
            if not macaddress:
                continue
            macaddresses.append(macaddress)
        department = row[14].strip()
        # Test if there are any non-alphanumeric characters except -
        if not serial.replace('-', '').isalnum():
            serial = ''
        if not serial and not macaddresses:
            logging.error(f"No serial number or MAC address found for {name}. Cannot uniquely identify asset.")
            continue
        if not serial:
            serial = macaddresses[0].replace(':', '').upper()
        try:
            # Check Snipe-IT for the asset
            asset = (Hardware(api=api,
                              name=name,
                              serial=serial,
                              asset_tag=f'IMPORT-{serial}',
                              model_id=DEFAULTS['model_id'],
                              notes=f"Imported by CSV - {owner}",
                              custom_fields=copy.deepcopy(DEFAULTS['custom_fields']),
                              status_id=DEFAULTS['status_id_pending']
                              )
                     .set_custom_field("Operating System", operating_system)
                     .set_custom_field("OS Type", os_type)
                     .set_custom_field("IP Address", ip)
                     .get_by_assettag()
                     .get_by_serial()
                     .get_by_mac(macaddresses)
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
    for file in listdir(INPUT_DIR):
        if file.endswith(".xls") or file.endswith(".csv") or file.endswith(".xlsx"):
            full_path = path.join(INPUT_DIR, file)
            errors = csv2snipe(full_path)
            if errors:
                logging.error(f"Errors occurred while processing {file}")
                logging.debug(errors)
                move(path.join(INPUT_DIR, file), path.join(OUTPUT_DIR, file))
            else:
                logging.info(f"Processed {file} successfully")
                move(path.join(INPUT_DIR, file), path.join(OUTPUT_DIR, file))


if __name__ == '__main__':
    main()
