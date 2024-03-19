#!/usr/bin/env python3
# ansible2snipe - Inventory Import
#
# ABOUT:
#   This program is designed to create assets into snipe-it using api calls. For more information
#   about both of these products, please visit their respective
#   websites:
#       https://ansible.com/
#       https://snipeitapp.com
#
# LICENSE:
#   MIT
#
# CONFIGURATION:
#   These settings are commonly found in the settings.conf file.
#
#   You can associate Snipe-IT hardware keys in the [api-mapping] section, to an Ansible facts key, so it associates
#   the jamf values into Snipe-IT. The default example associates information that exists by default in both
#   Snipe-IT and Ansible.  The Key value is the exact name of the Snipe-IT key name.
#   Note that MAC Address are a custom value in SNIPE by default, and you can use it as an example.
#
#   [api-mapping]
#       name = general name
#       _snipeit_mac_address_1 = ansible_mac_address
#       _snipeit_custom_name_1234567890 = ansible_dict ansible_key
#
from __future__ import annotations

import copy
import logging
from configparser import RawConfigParser
from json import loads as json_str_to_dict
from typing import Iterable

from jinja2 import Template
from jinja2.nativetypes import NativeEnvironment

from snipeit_api.api import SnipeITApi
from snipeit_api.defaults import DEFAULTS
from snipeit_api.helpers import clean_tag, clean_mac, filter_list
from snipeit_api.models import Hardware, Manufacturers, Models, Users

version = "0.1"
CONFIG = RawConfigParser()
logging.basicConfig(level=logging.ERROR)


def get_os_config_value(os, config_key, data):
    return get_config_value(CONFIG[f"{os}-api-mapping"][config_key], data)


# Function to recursively get keys from a dictionary
def get_config_value(config_key, data, invalid_values=None):
    logging.debug(f"Getting config value for {config_key}")
    # logging.debug(f"Data: {data}")
    split_key = config_key.split("|", 1)
    search_keys = split_key[0].strip().split(" ")
    j2_str = None
    if len(split_key) > 1:
        j2_str = split_key[1].strip()
        logging.debug(f"Jinja2 template: {j2_str}")

    value = data
    for key in search_keys:
        try:
            # Try to convert to int, settings file returns strings,
            # but if we want to traverse a list we need an int
            key = int(key)
        except ValueError:
            logging.debug(f"{key} is not an integer")
        try:
            value = value[key]
        except (KeyError, IndexError, TypeError):
            # JAMF is not consistent with return types
            logging.info(f"{key} does not exist or is empty")
            # logging.debug(f"Key value: {value}")
            value = None
            break

    if invalid_values and value in invalid_values:
        value = None

    if j2_str:
        environment = NativeEnvironment()
        template = environment.from_string(j2_str)
        value = template.render(var=value, data=data, clean_mac=clean_mac, clean_tag=clean_tag)
    logging.debug(f"Got value {value} for {config_key}")
    return value


def extract_api_mapping(os: str, asset_data: Iterable) -> dict:
    return_dict = {}
    for snipekey in CONFIG[f"{os}-api-mapping"]:
        if not snipekey.startswith("_snipeit_"):
            continue

        value = get_os_config_value(os, snipekey, asset_data)
        if value:
            logging.debug(f"Setting {snipekey} to {value}")
            return_dict[snipekey] = value
    return return_dict


def main():
    # Find a valid settings.conf file.
    CONFIG.read("settings.conf")
    if 'snipe-it' not in set(CONFIG):
        logging.debug("No valid CONFIG found in current folder.")
        logging.error(
            "No valid settings.conf was found. We'll need to quit while you figure out where the settings are at. "
            "You can check the README for valid locations.")
        raise SystemExit("Error: No valid settings.conf - Exiting.")

    api = SnipeITApi(url=CONFIG['snipe-it']['url'],
                     api_key=CONFIG['snipe-it']['apikey'])

    # Open STDIN and read the JSON
    with open(0, 'r') as f:
        ansible_json = f.read()

    # Parse the JSON
    ansible_data = json_str_to_dict(ansible_json)
    os = ansible_data['os_family']
    logging.info(f"Starting to update {os} inventory.")
    # Get category
    if f"{os}-api-mapping" not in CONFIG:
        logging.error(f"No api-mapping section found for {os}")
        raise SystemExit("Error: Missing or invalid settings in settings.conf - Exiting.")

    computer_name = str(ansible_data['hostname']).split('.')[0].upper()

    serial = get_os_config_value(os, 'serial', ansible_data)
    asset_tag = get_os_config_value(os, 'asset_tag', ansible_data)
    model = get_os_config_value(os, 'model', ansible_data)
    manufacturer = get_os_config_value(os, 'manufacturer', ansible_data)
    mac_addresses = get_os_config_value(os, 'mac_addresses', ansible_data)
    os_type = get_os_config_value(os, 'os_type', ansible_data)
    operating_system = get_os_config_value(os, 'operating_system', ansible_data)
    os_version = get_os_config_value(os, 'os_version', ansible_data)
    os_build = get_os_config_value(os, 'os_build', ansible_data)
    current_user = get_os_config_value(os, 'current_user', ansible_data)
    ram = int(float(get_os_config_value(os, 'ram', ansible_data)))
    cpu = get_os_config_value(os, 'cpu', ansible_data)
    storage = get_os_config_value(os, 'storage', ansible_data)
    domain = get_os_config_value(os, 'domain', ansible_data)
    org_unit = get_os_config_value(os, 'org_unit', ansible_data)
    edr = get_os_config_value(os, 'edr', ansible_data)
    ip_address = get_os_config_value(os, 'ip_address', ansible_data)

    if not asset_tag and not serial and not mac_addresses:
        logging.error(f"No valid asset_tag, serial, or mac found for {computer_name}. Skipping.")
        return

    manufacturer = Manufacturers(api=api, name=manufacturer).get_by_name().create()
    model_data = {"manufacturer_id": manufacturer.id, "name": model}
    model = Models(api=api, category_id=DEFAULTS['category_id'], fieldset_id=DEFAULTS['fieldset_id']).get_by_name(
        model).populate(model_data).create()

    hardware_data = {
        "name": computer_name,
        "serial": serial,
        "asset_tag": asset_tag,
        "model_id": model.id,
        "status_id": 4,
    }
    print(type(mac_addresses))
    new_hw = (Hardware(api=api,
                       name=computer_name,
                       asset_tag=asset_tag,
                       serial=serial,
                       custom_fields=copy.deepcopy(DEFAULTS['custom_fields'])
                       )
              .get_by_assettag()
              .get_by_serial()
              .get_by_mac(mac_addresses)
              .store_state()
              .populate(hardware_data)
              .populate_mac(mac_addresses))

    # Amend domain
    old_domain = new_hw.get_custom_field("Domain").split(", ")
    new_domain = []
    if domain:  # Sometimes it is empty
        new_domain = [domain.upper()]
    new_hw.set_custom_field("Domain", ", ".join(filter_list(new_domain + old_domain)))

    management = ['Ansible']
    old_management = new_hw.get_custom_field("Management")
    if not old_management:
        # Filter list to remove empty, duplicate values and sort in order
        new_hw.set_custom_field("Management", ', '.join(filter_list(management)))
    else:
        old_management_list = old_management.split(", ")
        # Add the new values to the old values
        new_hw.set_custom_field("Management", ', '.join(filter_list(old_management_list + management)))

    if not new_hw.get_custom_field("EDR"):
        new_hw.set_custom_field("EDR", edr)
    else:
        # Add the new values to the old values
        new_hw.set_custom_field("EDR", ', '.join(
            filter_list(new_hw.get_custom_field("EDR").split(", ") + [edr])))

    logging.debug(new_hw.to_dict() | new_hw.get_custom_fields())

    if org_unit:
        new_hw.set_custom_field("Org. Unit", org_unit)

    # Make sure to filter out the unknowns but maintain the domain
    if clean_tag(current_user):
        # Set the raw value for last user
        new_hw.set_custom_field("Last User", current_user)
        # Users will strip the domain
        user = Users(api=api, username=current_user).get_by_username()
        if user.id:
            if user.department and not new_hw.get_custom_field("Department"):
                new_hw.set_custom_field("Department", user.department.name)
            if user.department not in DEFAULTS['techs'] and user.username not in DEFAULTS['techs']:
                try:
                    new_hw.upsert().checkout_to_user(user, note="From Ansible")
                except ValueError:
                    logging.error(f"Failed to check out {new_hw.name} to {user.username}")
            # If we have an empty department, then update it

    (new_hw
     .set_custom_field("Operating System", operating_system)
     .set_custom_field("OS Version", os_version)
     .set_custom_field("OS Build", os_build)
     .set_custom_field("OS Type", os_type)
     .set_custom_field("IP Address", ip_address)
     .set_custom_field("RAM", ram)
     .set_custom_field("CPU", cpu)
     .set_custom_field("Storage", storage)
     .upsert())


if __name__ == "__main__":
    main()
