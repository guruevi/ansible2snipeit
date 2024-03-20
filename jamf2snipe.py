#!/usr/bin/env python3
from __future__ import annotations

import copy
import logging
from configparser import RawConfigParser
from datetime import datetime, timedelta
from time import sleep

from requests import Response, get, post, patch

from snipeit_api.api import SnipeITApi
from snipeit_api.defaults import DEFAULTS
from snipeit_api.helpers import filter_list, query_apple_warranty, print_progress, clean_tag
from snipeit_api.models import Hardware, Models, Manufacturers, Users

logging.basicConfig(level=logging.ERROR)
CONFIG = RawConfigParser()
logging.debug("Checking for a settings.conf ...")
CONFIG.read("settings.conf")
snipeit_apiurl = CONFIG.get('snipe-it', 'url')
snipeit_apikey = CONFIG.get('snipe-it', 'apikey')
# Get the techs from the config file
DEFAULTS['techs'] = CONFIG.get('snipe-it', 'techs').split(" ")

snipe_api = SnipeITApi(url=snipeit_apiurl, api_key=snipeit_apikey)
JAMF_HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json'}
JAMF_EXPIRES: datetime = datetime.now()


# Use Basic Auth to request a Jamf Token.
def request_jamf_token():
    global JAMF_EXPIRES, JAMF_HEADERS
    # Tokens expire after 30 minutes (new API)
    api_url = f"{CONFIG['jamf']['url']}/api/v1/auth/token"

    # We assume it may take ~15 seconds to get a token
    if ('Authorization' in JAMF_HEADERS and JAMF_HEADERS['Authorization'] and
            JAMF_EXPIRES > datetime.now() + timedelta(seconds=15)):
        api_url = f"{CONFIG['jamf']['url']}/api/v1/auth/keep-alive"

    # No hook for this api call.
    logging.debug(f'Calling for a token against: {api_url}')

    response = api_call(api_url,
                        auth=(CONFIG['jamf']['username'], CONFIG['jamf']['password']),
                        method="POST",
                        headers=JAMF_HEADERS)

    response_json = response.json()
    # No hook for this API call.
    if response.status_code == 200:
        logging.debug("Got back a valid 200 response code.")
        # DEV: Only enable this if you want to see the token in the log.
        # logging.debug(jsonresponse)
        try:
            # Parse this 2022-01-24T21:35:20.373Z or  2023-10-12T00:09:38Z
            if "." in response_json['expires']:
                JAMF_EXPIRES = datetime.strptime(response_json['expires'], "%Y-%m-%dT%H:%M:%S.%fZ")
            else:
                JAMF_EXPIRES = datetime.strptime(response_json['expires'], "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            logging.error(f"Timestamp in {response_json} is invalid - exiting")
            raise SystemExit("Unable to grok Jamf Timestamp - Exiting")

        logging.debug(f"Token expires at {JAMF_EXPIRES}")

        # The headers are also global, because they get used elsewhere.
        logging.info("Setting new jamf headers with bearer token")
        JAMF_HEADERS['Authorization'] = f'Bearer {response_json["token"]}'
    else:
        logging.error("Could not obtain a token for use, please check your username and password.")
        raise SystemExit("Unable to obtain Jamf Token")


# Function to make the API call for all JAMF devices
# Returns a list of all computers in JAMF with inventory details
# Pass filter_rsql in rsql format - e.g. "general.assetTag==123456"
def get_jamf_computers(filter_rsql=None):
    # Sections the user wants to retrieve, we require general and hardware for getting serial/asset numbers
    sections = {"GENERAL", "HARDWARE", "PURCHASING", "USER_AND_LOCATION", "STORAGE", "OPERATING_SYSTEM"}

    search_query = "?section=" + "&section=".join(sections)

    if filter_rsql:
        search_query += f"&filter={filter_rsql}"

    logging.info("Fetching JAMF computers...")
    return get_jamf_paginated_objects(f"/api/v1/computers-inventory{search_query}")


# Function to make an API call with pagination, returning all objects
def get_jamf_paginated_objects(api, page=0):
    # Function arguments should not be mutable
    page_size = 500

    page_add = f"&page={page}&page-size={page_size}"
    response = jamf_api_call(f"{api}{page_add}", method="GET")

    if "results" not in response or not response['results'] or "totalCount" not in response:
        logging.info("Received an invalid response from Jamf, exiting")
        logging.debug(response)
        raise SystemExit("Invalid response from Jamf")

    current = response['results']
    logging.debug(f"Received: {len(current)} objects")

    page += 1
    if (page_size * page) < response['totalCount']:
        current.extend(get_jamf_paginated_objects(api, page))

    return current


# Function to make the API call for all JAMF mobile devices
def get_jamf_mobiles(filter_rsql=None):
    # Sections the user wants to retrieve, we require general and hardware for getting serial/asset numbers
    sections = {"GENERAL", "HARDWARE", "USER_AND_LOCATION", "PURCHASING"}

    search_query = "?section=" + "&section=".join(sections)

    if filter_rsql:
        search_query += f"&filter={filter_rsql}"

    logging.info("Fetching JAMF computers...")
    return get_jamf_paginated_objects(f"/api/v2/mobile-devices/detail{search_query}")


def jamf_api_call(endpoint, payload=None, method="GET", backoff=0):
    api_url = f"{CONFIG['jamf']['url']}{endpoint}"

    if JAMF_EXPIRES < datetime.now() + timedelta(minutes=2):
        logging.info("Token expiring soon or already expired, requesting new token")
        request_jamf_token()

    response = api_call(api_url, payload, method, JAMF_HEADERS)

    if response.status_code == 200:
        return response.json()

    if response.status_code == 429:
        backoff += 1
        backoff = backoff * 30
        logging.warning(f'JAMF Pro Ratelimit exceeded: pausing {backoff}s')
        sleep(backoff)
        logging.info("Finished waiting. Retrying lookup...")
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
    complete_list: list[dict] = get_jamf_mobiles()
    complete_list.extend(get_jamf_computers())
    total = len(complete_list)
    current = 0

    # Make sure we have a good list.
    logging.debug(f'Received a list of JAMF assets that had {total} entries.')
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
            jamf_name = get_str("displayName", general)
            asset_tag_prefix = 'JAMF-M-'
            jamf_storage = get_int("capacityMb", hardware)
            jamf_os = get_str('deviceType', jamf_asset)
            jamf_os_version = get_str('osVersion', general)
            jamf_os_build = get_str('osBuild', general)
            jamf_ip = get_str('ipAddress', general)
        else:
            jamf_id = jamf_asset['id']
            jamf_name = general.get("name", '')
            jamf_usernames = get_list("localUserAccounts", jamf_asset)
            for user in jamf_usernames:
                if 'homeDirectory' not in user:
                    continue
                # Home directory starts with /Users
                if user['homeDirectory'].startswith("/Users") and user['username'] not in ["its_local", "isdadmin"]:
                    jamf_username = user['username']
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

        asset = {
            'name': jamf_name,
            'serial_number': serial_number,
            'asset_tag': asset_tag,
            'model_id': model.id,
        }

        new_hw = (Hardware(api=snipe_api,
                           name=jamf_name,
                           asset_tag=asset_tag,
                           serial=serial_number,
                           custom_fields=copy.deepcopy(DEFAULTS['custom_fields']),
                           status_id=DEFAULTS['status_id_deployed']
                           )
                  .get_by_assettag()
                  .get_by_serial()
                  .get_by_mac(raw_macs)
                  .store_state()
                  .populate(asset)
                  .populate_mac(raw_macs))

        if new_hw.status_id == DEFAULTS['status_id_pending']:
            new_hw.status_id = DEFAULTS['status_id_deployed']

        purchase_cost = purchasing.get('purchasePrice', 0)
        if not new_hw.purchase_cost and purchase_cost:
            setattr(new_hw, 'purchase_cost', purchase_cost)

        lease_date = purchasing.get('leaseDate', '')
        purchase_date = purchasing.get('poDate', lease_date)
        if not new_hw.purchase_date:
            if purchase_date:
                setattr(new_hw, 'purchase_date', purchase_date)
                warranty_ends = purchasing.get('warrantyDate', '')
                if warranty_ends:
                    months = (datetime.strptime(warranty_ends, "%Y-%m-%d") - datetime.strptime(purchase_date,
                                                                                               "%Y-%m-%d")).days // 30
                    setattr(new_hw, 'warranty_months', months)
            else:
                logging.debug(f"Asset has no purchase date, making a guess")
                purchase_date = query_apple_warranty(serial_number, model_jamf_name)
                if purchase_date:
                    setattr(new_hw, 'purchase_date', purchase_date.strftime("%Y-%m-%d"))
                    setattr(new_hw, 'warranty_months', 36)

        new_hw.set_custom_field("CPU", jamf_cpu)
        new_hw.set_custom_field("RAM", jamf_ram)
        new_hw.set_custom_field("Storage", jamf_storage)

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
            user = Users(api=snipe_api, username=jamf_username).get_by_username()
            if user.id and user.department not in DEFAULTS['techs'] and user.username not in DEFAULTS['techs']:
                try:
                    new_hw.upsert().checkout_to_user(user, note="From JAMF")
                except ValueError:
                    logging.error(f"Failed to checkout {new_hw.name} to {user.username}")
            # If we have an empty department, then update it
            if (new_hw.assigned_to and new_hw.assigned_to.id and
                    user.department and not new_hw.get_custom_field("Department")):
                new_hw.set_custom_field("Department", user.department.name)
            # Sometimes last domain user is the hostname, user.username is cleaned, regardless whether it is valid
            # We check for user.id if it is a valid user
            if (not new_hw.get_custom_field("Last User")
                    or ((user.id and user.username != new_hw.name)
                        and (jamf_username not in new_hw.get_custom_field("Last User")))):
                new_hw.set_custom_field("Last User", jamf_username)

        new_hw.upsert()
        print_progress(current, total)
        current += 1


if __name__ == "__main__":
    main()
