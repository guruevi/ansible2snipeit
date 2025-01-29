#!/usr/bin/env python3
from __future__ import annotations

import copy
import logging
from configparser import RawConfigParser
from datetime import datetime, timedelta, timezone
from itertools import chain
from time import sleep
from typing import Generator

from requests import Response, get, post, patch

from snipeit_api.api import SnipeITApi
from snipeit_api.defaults import DEFAULTS
from snipeit_api.helpers import filter_list, query_apple_warranty, print_progress, clean_tag, clean_user, \
    parse_isoformat
from snipeit_api.models import Hardware, Models, Manufacturers, Users

logging.basicConfig(level=logging.INFO)
CONFIG = RawConfigParser()
logging.debug("Checking for a settings.conf ...")
CONFIG.read("settings.conf")
snipeit_apiurl = CONFIG.get('snipe-it', 'url')
snipeit_apikey = CONFIG.get('snipe-it', 'apikey')
# Get the techs from the config file
DEFAULTS['techs'] = CONFIG.get('snipe-it', 'techs').split(" ")

snipe_api = SnipeITApi(url=snipeit_apiurl, api_key=snipeit_apikey)
JAMF_HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json'}
JAMF_EXPIRES: datetime = datetime.now(timezone.utc)


# Use Basic Auth to request a Jamf Token.
def request_jamf_token():
    global JAMF_EXPIRES, JAMF_HEADERS

    # If we have a token and it is not expired, don't request a new one
    if JAMF_EXPIRES > datetime.now(timezone.utc) + timedelta(seconds=120):
        return JAMF_HEADERS

    api_url = f"{CONFIG['jamf']['url']}/api/v1/auth/keep-alive"
    auth = None

    # If we have a token, we can use the keep-alive endpoint if it hasn't expired
    if 'Authorization' not in JAMF_HEADERS or not JAMF_HEADERS['Authorization']:
        # Tokens expire after 20 minutes (new API)
        api_url = f"{CONFIG['jamf']['url']}/api/v1/auth/token"
        auth = (CONFIG['jamf']['username'], CONFIG['jamf']['password'])

    logging.info(f'Calling for a token against: {api_url}')

    response = api_call(api_url,
                        auth=auth,
                        method="POST",
                        headers=JAMF_HEADERS)

    response_json = response.json()
    if response.status_code != 200:
        logging.info(f"Received an invalid response from Jamf: {response.status_code} - {response_json}")
        logging.error("Could not obtain a token for use, please check your username and password.")
        raise SystemExit("Unable to obtain Jamf Token")

    # DEV: Only enable this if you want to see the token in the log.
    # logging.debug(jsonresponse)
    try:
        JAMF_EXPIRES = parse_isoformat(response_json['expires'])
    except ValueError:
        logging.error(f"Timestamp in {response_json} is invalid - exiting")
        raise SystemExit("Unable to grok Jamf Timestamp - Exiting")

    logging.info(f"Token expires at {JAMF_EXPIRES}")

    # The headers are also global, because they get used elsewhere.
    JAMF_HEADERS['Authorization'] = f'Bearer {response_json["token"]}'
    return JAMF_HEADERS


# Function to make the API call for all JAMF devices
# Returns a list of all computers in JAMF with inventory details
# Pass filter_rsql in rsql format - e.g. "general.assetTag==123456"
def get_jamf_computers(filter_rsql=None):
    # Sections the user wants to retrieve, we require general and hardware for getting serial/asset numbers
    sections = {"GENERAL", "HARDWARE", "PURCHASING", "USER_AND_LOCATION", "STORAGE", "OPERATING_SYSTEM",
                "LOCAL_USER_ACCOUNTS", "LICENSED_SOFTWARE"}

    search_query = "?section=" + "&section=".join(sections)

    if filter_rsql:
        search_query += f"&filter={filter_rsql}"

    logging.info("Fetching JAMF computers...")
    return get_jamf_paginated_objects(f"/api/v1/computers-inventory{search_query}")


TOTALCOUNT = 0
PAGE_SIZE = 50


# Function to make an API call with pagination, returning all objects
def get_jamf_paginated_objects(api, page=0):
    global TOTALCOUNT
    global PAGE_SIZE

    while True:
        logging.debug(f"Started page {page}/{TOTALCOUNT // PAGE_SIZE} at {datetime.now()}")
        page_add = f"&page={page}&page-size={PAGE_SIZE}"
        response = jamf_api_call(f"{api}{page_add}", method="GET")

        if "results" not in response or not response['results'] or "totalCount" not in response:
            logging.info("Received an invalid response from Jamf, exiting")
            raise SystemExit("Invalid response from Jamf")

        TOTALCOUNT = response['totalCount']
        current = response['results']
        logging.debug(f"Received: {len(current)} objects")

        for item in current:
            yield item

        page += 1
        if (PAGE_SIZE * page) >= response['totalCount']:
            break


# Function to make the API call for all JAMF mobile devices
def get_jamf_mobiles(filter_rsql=None):
    # Sections the user wants to retrieve, we require general and hardware for getting serial/asset numbers
    sections = {"GENERAL", "HARDWARE", "USER_AND_LOCATION", "PURCHASING"}

    search_query = "?section=" + "&section=".join(sections)

    if filter_rsql:
        search_query += f"&filter={filter_rsql}"

    logging.info("Fetching JAMF mobiles...")
    return get_jamf_paginated_objects(f"/api/v2/mobile-devices/detail{search_query}")


def jamf_api_call(endpoint, payload=None, method="GET", backoff=0):
    global JAMF_HEADERS
    global JAMF_EXPIRES

    if backoff > 5:
        logging.error("JAMF API call failed after 5 retries")
        raise SystemExit("JAMF API call failed after 5 retries")

    api_url = f"{CONFIG['jamf']['url']}{endpoint}"

    request_jamf_token()

    response = api_call(api_url, payload, method, JAMF_HEADERS)

    if response.status_code == 200:
        return response.json()

    if response.status_code == 429:
        backoff += 1
        time_backoff = backoff * 30
        logging.warning(f'JAMF Pro Ratelimit exceeded: pausing {time_backoff}s')
        sleep(time_backoff)
        return jamf_api_call(endpoint, payload, method, backoff)

    if response.status == 401:
        logging.error("JAMF API call failed with 401, refreshing token")
        # This means we likely are reusing an expired token, expired tokens cannot be re-used.
        JAMF_EXPIRES = datetime.now(timezone.utc)
        del JAMF_HEADERS['Authorization']
        backoff += 1
        return jamf_api_call(endpoint, payload, method, backoff)

    logging.error(f"JAMF responded with error code:{response.text}")
    logging.debug(f"{response.status_code} - {response.content}")
    raise SystemExit("JAMF API call failed")


# Helper function to call an API
def api_call(api_url, json=None, method="GET", headers=None, auth=None) -> Response:
    logging.debug(f"Calling {api_url} with method {method} and payload {json}")

    if method == "GET":
        response = get(api_url, headers=headers, json=json)
    elif method == "POST":
        response = post(api_url, auth=auth, headers=headers, json=json)
    elif method == "PATCH":
        response = patch(api_url, headers=headers, json=json)
    else:
        raise SystemExit(f"Unknown method {method}")

    return response


def get_dict(key: str, props: dict):
    value = props.get(key, {}) or {}
    if type(value) is not dict:
        logging.error(f"Expected {key} to be a dict, but got {type(value)}")
        return {}
    return value


def get_str(key: str, props: dict):
    value = props.get(key, '') or ''
    return value


def get_int(key: str, props: dict):
    value: str | int = props.get(key, 0) or 0
    try:
        value = int(value)
    except ValueError:
        value = 0
    return value


def get_list(key: str, props: dict):
    value: list = props.get(key, []) or []
    if type(value) is not list:
        logging.error(f"Expected {key} to be a list, but got {type(value)}")
        return []
    return value


def main():
    # These functions do not run until you need an item from the generator
    mobile_list: Generator = get_jamf_mobiles()
    computer_list: Generator = get_jamf_computers()
    complete_list = chain(mobile_list, computer_list)
    current_count = 0
    manufacturer = Manufacturers(api=snipe_api).get_by_name("Apple").create()

    for jamf_asset in complete_list:
        # We can differentiate between a computer and a mobile device by the presence of a mobileDeviceId
        logging.debug(f"Processing JAMF asset: {jamf_asset}")
        custom_fieldset_id = DEFAULTS['fieldset_id']
        category_id = DEFAULTS['category_id']
        asset_tag_prefix = 'JAMF-'
        jamf_cpu = None
        jamf_ram = 0
        hardware = get_dict("hardware", jamf_asset)
        general = get_dict("general", jamf_asset)
        storage = get_dict("storage", jamf_asset)
        purchasing = get_dict("purchasing", jamf_asset)
        operating_system = get_dict("operatingSystem", jamf_asset)
        jamf_username = ''
        jamf_ip = ''
        jamf_domain = ''

        if "mobileDeviceId" in jamf_asset:
            jamf_id = get_str("mobileDeviceId", jamf_asset)
            custom_fieldset_id = DEFAULTS['mobile_fieldset_id']
            category_id = DEFAULTS['mobile_category_id']
            jamf_userloc = get_dict("userAndLocation", jamf_asset)
            jamf_username = jamf_userloc.get("username", '')
            jamf_name = get_str("displayName", general).strip()
            asset_tag_prefix = 'JAMF-M-'
            jamf_storage = get_int("capacityMb", hardware)
            jamf_os = get_str('deviceType', jamf_asset)
            jamf_os_version = get_str('osVersion', general)
            jamf_os_build = get_str('osBuild', general)
            jamf_ip = get_str('ipAddress', general)
            jamf_licensed_software = []
        else:
            jamf_id = jamf_asset['id']
            jamf_name = general.get("name", '')
            jamf_usernames = get_list("localUserAccounts", jamf_asset)
            for user in jamf_usernames:
                if 'homeDirectory' not in user or not user['homeDirectory']:
                    continue
                # Home directory starts with /Users
                if (user['homeDirectory'].startswith("/Users") and
                        user['username'].lower() not in DEFAULTS['techs'] and
                        'admin' not in user['username'].lower()):
                    jamf_username = clean_user(user['username'])
                    break
            jamf_ram = hardware.get('totalRamMegabytes', 0)
            jamf_disks = get_list("disks", storage)
            jamf_storage = 0
            # Add up all the disk sizes because they are not necessarily in order
            for disk in jamf_disks:
                if 'sizeMegabytes' not in disk:
                    continue
                jamf_storage += disk['sizeMegabytes']
            jamf_cpu = hardware.get('processorType', '')
            ad_status = get_str("activeDirectoryStatus", operating_system)
            if ad_status and ad_status != "Not Bound":
                jamf_domain = ad_status.split('.')[0].upper()
            jamf_os = get_str('name', operating_system)
            jamf_os_version = get_str('version', operating_system)
            jamf_os_build = get_str('build', operating_system)
            jamf_licensed_software = get_list("licensedSoftware", jamf_asset)
        logging.debug(f"Processing JAMF ID: {jamf_id}")

        model_jamf_id = get_str('modelIdentifier', hardware)
        model_jamf_name = get_str('model', hardware)
        serial_number = get_str('serialNumber', hardware)
        asset_tag = hardware.get('assetTag', f"{asset_tag_prefix}{jamf_id}")

        # Get MAC addresses
        raw_macs = [hardware.get('wifiMacAddress', ''), hardware.get('bluetoothMacAddress', ''),
                    hardware.get('macAddress', ''), hardware.get('altMacAddress', '')]

        if clean_tag(model_jamf_id):
            model = (Models(api=snipe_api, model_number=model_jamf_id)
                     .get_by_model_number()
                     .populate({"name": model_jamf_name,
                                "model_number": model_jamf_id,
                                "manufacturer_id": manufacturer.id,
                                "category_id": category_id,
                                "fieldset_id": custom_fieldset_id,
                                "eol": int(CONFIG['snipe-it'].get('default_eol', "84"))
                                })
                     .create())
        else:
            model = Models(api=snipe_api, name='Unspecified').get_by_name()

        new_hw = (Hardware(api=snipe_api,
                           name=jamf_name,
                           asset_tag=asset_tag,
                           serial=serial_number,
                           custom_fields=copy.deepcopy(DEFAULTS['custom_fields']),
                           status_id=DEFAULTS['status_id_deployed'],
                           model_id=model.id
                           )
                  .get_by_serial()
                  .get_by_mac(raw_macs)
                  .get_by_asset_tag()
                  .store_state()
                  .populate_mac(raw_macs))

        if new_hw.status_id == DEFAULTS['status_id_pending']:
            new_hw.status_id = DEFAULTS['status_id_deployed']

        if new_hw.status_id == 5:
            new_hw.status_id = 4

        purchase_cost = purchasing.get('purchasePrice', 0)
        if not new_hw.purchase_cost and purchase_cost:
            setattr(new_hw, 'purchase_cost', purchase_cost)

        lease_date = purchasing.get('leaseDate', '')
        purchase_date = purchasing.get('poDate', lease_date)
        warranty_ends = purchasing.get('warrantyDate', '')
        if not new_hw.purchase_date:
            if purchase_date:
                setattr(new_hw, 'purchase_date', purchase_date)
            else:
                logging.debug(f"Asset has no purchase date, making a guess")
                purchase_date = query_apple_warranty(serial_number, model_jamf_name)
                if purchase_date:
                    setattr(new_hw, 'purchase_date', purchase_date.strftime("%Y-%m-%d"))
                    setattr(new_hw, 'warranty_months', 36)
                else:
                    logging.info(f"Could not find a purchase date for {model_jamf_name}")

        if warranty_ends and purchase_date:
            months = (datetime.strptime(warranty_ends, "%Y-%m-%d") - datetime.strptime(purchase_date,
                                                                                       "%Y-%m-%d")).days // 30
            setattr(new_hw, 'warranty_months', months)

        new_hw.set_custom_field("CPU", jamf_cpu)
        new_hw.set_custom_field("RAM", jamf_ram)
        new_hw.set_custom_field("Storage", str(jamf_storage))

        # Don't collect public network information
        if (jamf_ip.startswith("10.") or jamf_ip.startswith("192.168") or jamf_ip.startswith("172.16") or
                jamf_ip.startswith("172.17") or jamf_ip.startswith("172.18") or jamf_ip.startswith("172.19") or
                jamf_ip.startswith("172.2") or jamf_ip.startswith("172.30") or jamf_ip.startswith("172.31")):
            new_hw.set_custom_field("IP Address", jamf_ip)

        new_hw.set_custom_field("OS Type", "Other")
        new_hw.set_custom_field("Operating System", jamf_os)
        # Sometimes JAMF returns an extra .0 at the end of the version, and sometimes it doesn't, it is not consistent
        if jamf_os_version.endswith(".0"):
            jamf_os_version = jamf_os_version[:-2]
        new_hw.set_custom_field("OS Version", jamf_os_version)
        if jamf_os_build.endswith(".0"):
            jamf_os_build = jamf_os_build[:-2]
        new_hw.set_custom_field("OS Build", jamf_os_build)
        # Values are "Yes", "No", "Unidirectional Outbound"
        # Don't overwrite a specific value with a general value
        if new_hw.get_custom_field("Internet") != "Unidirectional Outbound":
            # JAMF lives in the cloud, so Internet is required
            if new_hw.get_custom_field("Internet") != "Yes":
                new_hw.set_custom_field("Internet", "Yes")

        # All Apple devices come with XProtect
        if not jamf_licensed_software:
            jamf_licensed_software = [{"name": "XProtect", 'id': '0'}]
        # Filter out the names from jamf_licensed_software
        edr_list = [x['name'] for x in jamf_licensed_software if x['name'] in ["Cylance PROTECT", "CrowdStrike Falcon"]]
        new_hw.set_custom_field("EDR", ', '.join(filter_list(edr_list)))

        if not new_hw.get_custom_field("Domain"):
            new_hw.set_custom_field("Domain", jamf_domain)
        else:
            old_domain_list: list = new_hw.get_custom_field("Domain").split(", ")
            # Add the new values to the old values
            new_hw.set_custom_field("Domain", ', '.join(filter_list(old_domain_list + [jamf_domain])))

        if not new_hw.get_custom_field("Management"):
            new_hw.set_custom_field("Management", "JAMF")
        else:
            old_management_list: list = new_hw.get_custom_field("Management").split(", ")
            # Add the new values to the old values
            new_hw.set_custom_field("Management", ', '.join(filter_list(old_management_list + ['JAMF'])))

        if jamf_username:
            new_hw.set_custom_field("Last User", jamf_username)

        new_hw.upsert()
        print_progress(current_count, TOTALCOUNT)
        current_count += 1


if __name__ == "__main__":
    main()
