#!/usr/bin/env python3
import copy
import logging
from configparser import RawConfigParser
from os import getenv
from time import sleep

from medigate_api import DevicesApi, Configuration, ApiClient
from medigate_api.models import GetDevicesParameters
from medigate_api.rest import ApiException

from snipeit_api.defaults import DEFAULTS
from snipeit_api.api import SnipeITApi
from snipeit_api.helpers import filter_list, filter_list_str, filter_list_first, clean_ip, clean_tag, print_progress, \
    clean_user, clean_edr, clean_mac
from snipeit_api.models import Hardware, Models, Category, Manufacturers, FieldSets, Users

logging.basicConfig(level=logging.INFO)
CONFIG = RawConfigParser()
logging.debug("Checking for a settings.conf ...")
CONFIG.read("settings.conf")
medigate_apikey = CONFIG.get('medigate', 'apikey')
medigate_apiurl = CONFIG.get('medigate', 'url')
snipeit_apiurl = CONFIG.get('snipe-it', 'url')
snipeit_apikey = CONFIG.get('snipe-it', 'apikey')
# Get the techs from the config file
DEFAULTS['techs'] = CONFIG.get('snipe-it', 'techs').split(" ")
# Get number of days from environment variable
DEFAULTS['days'] = int(getenv('DAYS', 30))  # Default to 30 if not set
DEFAULTS['first_or_last'] = getenv('FIRST_OR_LAST', 'last')  # Default to last if not set
if DEFAULTS['first_or_last'] not in ['first', 'last']:
    DEFAULTS['first_or_last'] = 'last'
# Set first_or_last to first_seen_list or last_seen_list
DEFAULTS['first_or_last'] = f"{DEFAULTS['first_or_last']}_seen_list"

snipe_api = SnipeITApi(url=snipeit_apiurl, api_key=snipeit_apikey)

fields = [
    # "ap_location_list",
    # "ap_name_list",
    "asset_id",
    # "assignees",
    "authentication_user_list",
    # "bssid_list",
    # "collection_interfaces",
    # "connection_type_list",
    # "device_type",
    # "device_type_family",
    "device_category",
    "device_name",
    "device_subcategory",
    "dhcp_hostnames",
    # "dhcp_last_seen_hostname",
    "domains",
    "endpoint_security_names",
    # "equipment_class",
    "handles_pii",
    # "http_hostnames",
    # "hw_version",
    "internet_communication",
    # "ip_assignment_list",
    "ip_list",
    "last_domain_user",
    # "last_domain_user_activity",
    # "local_name",
    # "machine_type",
    "mac_list",
    # "mac_oui_list",
    # "managed_by",
    "management_services",
    "manufacturer",
    # "mobility",
    "model",
    # "network_list",
    # "network_scope_list",
    "os_category",
    "os_eol_date",
    "os_name",
    "os_revision",
    # "os_subcategory",
    "os_version",
    # "other_hostnames",
    "phi",
    # "protocol_location_list",
    # "retired",
    "serial_number",
    # "site_name",
    # "snmp_hostnames",
    # "software_or_firmware_version",
    "ssid_list",
    "switch_group_name_list",
    "switch_port_list",
    "uid",
    "vlan_list",
    "vlan_name_list",
    # "windows_hostnames",
    # "windows_last_seen_hostname",
    # "wireless_encryption_type_list",
    # "wlc_location_list",
    # "wlc_name_list",
    # "switch_ip_list",
    # "switch_location_list",
    # "switch_mac_list",
    # "switch_port_description_list",
    # "vlan_description_list",
]

# Create an instance of the API class
mg_api = DevicesApi(ApiClient(Configuration(access_token=medigate_apikey)))
offset = 0
count = 0
limit = 100
current = 0

while offset <= count:
    parameters = GetDevicesParameters.from_dict({
        "filter_by": {
            "operation": "and",
            "operands": [
                {
                    "field": "network_list",
                    "operation": "in",
                    "value": ["Corporate"]
                },
                {
                    "field": "mac_list",
                    "operation": "is_not_null"
                },
                {
                    "field": "retired",
                    "operation": "in",
                    "value": [False]
                },
                {
                    "field": "mac_oui_list",
                    "operation": "not_in",
                    "value": ["Randomized Locally Administered Address"]
                },
                {
                    "field": DEFAULTS['first_or_last'],
                    "operation": "has_any_after_seconds_ago",
                    "value": DEFAULTS['days'] * 24 * 60 * 60  # 30 days
                }
            ]
        },
        "offset": offset,
        "limit": limit,
        "fields": fields,
        "include_count": True,

    })
    logging.debug(parameters)
    try:
        # Get devices
        api_response = mg_api.get_devices(parameters)
        if not count:
            count = api_response.count
            print(f"Total devices: {count}")
        offset += limit
    except ApiException as e:
        logging.error("Exception when calling DevicesApi->get_devices: %s\n" % e)
        sleep(60)  # Sleep for 60 seconds before trying again
        continue
    except (ValueError, KeyError):
        logging.error("Error parsing response")
        continue

    for device in api_response.devices:
        print_progress(current, count)
        current += 1
        logging.debug(device)
        model_config = {
            "manufacturer_id": DEFAULTS['manufacturer_id'],
            "category_id": DEFAULTS['category_id'],
            "fieldset_id": DEFAULTS['fieldset_id']
        }
        # Mapping from Medigate (key) to Snipe-IT custom fields (tuple with field name, default value and callable to
        # transform the value)
        asset_config_nonauth = {
            "status_id": DEFAULTS['status_id_pending'],
            "model_id": DEFAULTS['model_id'],
            "_snipeit_last_user_13": clean_user(filter_list_first(device['authentication_user_list'])),
            "_snipeit_operating_system_14": device['os_name'],
            "_snipeit_os_version_15": device['os_version'],
            "_snipeit_os_build_16": device['os_revision'],
            "_snipeit_domain_11": (', '.join(filter_list(device['domains']))).replace(".ROCHESTER.EDU", ""),
        }
        asset_config_auth = {
            "_snipeit_ip_address_5": clean_ip(filter_list_first(device['ip_list']).split("/")[0]),
            "_snipeit_switches_6": ', '.join(filter_list(device["switch_group_name_list"])),
            "_snipeit_switch_port_7": ', '.join(filter_list(device["switch_port_list"])),
            "_snipeit_ssid_8": ', '.join(filter_list(device["ssid_list"])),
            "_snipeit_vlan_9": ', '.join(filter_list_str(device["vlan_list"])),
            "_snipeit_vlan_name_10": ', '.join(filter_list(device["vlan_name_list"])),
        }
        # Apply clean_mac function to device['mac_list']
        mac_addresses = filter_list([clean_mac(mac) for mac in device['mac_list']])
        serial_number = clean_tag(device['serial_number'])

        if not mac_addresses and not serial_number:
            logging.error(
                f"No valid serial number or MAC address found for {device['device_name']}."
                f"Cannot uniquely identify asset."
                f"{device['mac_list']}"
                f"{device['serial_number']}"
            )
            continue

        # Remove empty values
        asset_config_nonauth = {k: v for k, v in asset_config_nonauth.items() if v}
        asset_config_auth = {k: v for k, v in asset_config_auth.items() if v}

        if device['device_category']:
            fieldset = FieldSets(api=snipe_api, name=device['device_category']).get_by_name().create()
            model_config['fieldset_id'] = fieldset.id
        if device['device_subcategory']:
            category = (Category(api=snipe_api, category_type="asset", name=device['device_subcategory'])
                        .get_by_name()
                        .create())
            model_config['category_id'] = category.id

        if device['manufacturer']:
            manufacturer = (Manufacturers(api=snipe_api, name=device['manufacturer'])
                            .get_by_name()
                            .create())
            model_config['manufacturer_id'] = manufacturer.id

        model = Models(api=snipe_api, name=device['model']).get_by_name().populate(model_config).create()
        asset_config_nonauth['model_id'] = model.id or DEFAULTS['model_id']
        assert asset_config_nonauth['model_id'] != 0

        hostname = filter_list_first(device['dhcp_hostnames']) or device['device_name']
        if not hostname:
            # Get IP address
            hostname = asset_config_auth['_snipeit_ip_address_5']
        hostname = hostname.split("\\")
        if len(hostname) > 1:
            hostname = hostname[1]
        else:
            hostname = hostname[0]

        # Get canonical name
        hostname = hostname.split(".")[0].upper()

        new_hw = (Hardware(api=snipe_api,
                           asset_tag=device['asset_id'] or device['uid'],
                           serial=serial_number,
                           name=hostname,
                           model_id=asset_config_nonauth['model_id'],
                           custom_fields=copy.deepcopy(DEFAULTS['custom_fields']))
                  .populate(asset_config_nonauth)
                  .get_by_asset_tag()
                  .get_by_serial()
                  .get_by_mac(device['mac_list'])
                  .get_by_name()
                  .store_state())

        # Populate all the custom fields
        new_hw.populate(asset_config_auth).populate_mac(device['mac_list'])

        # Override the OS type only if it is currently set to "Other" or empty
        if not new_hw.get_custom_field("OS Type") or new_hw.get_custom_field("OS Type") == "Other":
            new_hw.set_custom_field("OS Type", device['os_category'])

        # Amend domain
        old_domain = []
        if new_hw.get_custom_field("Domain"):
            old_domain = new_hw.get_custom_field("Domain").split(", ")
        new_domain = []
        for domain in device['domains']:
            if domain:  # Sometimes it is [None]
                new_domain.append(domain.replace(".ROCHESTER.EDU", ""))
        new_hw.set_custom_field("Domain", ", ".join(filter_list(new_domain + old_domain)))

        # Move from pending to deployed
        if 'UR' in new_hw.get_custom_field("Domain") and new_hw.status_id == DEFAULTS['status_id_pending']:
            new_hw.status_id = DEFAULTS['status_id_deployed']

        # Make sure we don't overwrite existing values
        if new_hw.get_custom_field("PII") != "Yes":
            new_hw.set_custom_field("PII", device['handles_pii'])

        # Values are "Yes", "No", "Unidirectional Outbound"
        # Don't overwrite a specific value with a general value
        if new_hw.get_custom_field("Internet") != "Unidirectional Outbound":
            # Don't overwrite a yes with a no
            if new_hw.get_custom_field("Internet") != "Yes":
                new_hw.set_custom_field("Internet", device['internet_communication'])
            elif device['internet_communication'] == "Unidirectional Outbound":
                new_hw.set_custom_field("Internet", "Unidirectional Outbound")

        # Values are "Transmits", "Stores", "Transmits and Stores"
        if device['phi'] and new_hw.get_custom_field("PHI") != device['phi']:
            transmit = False
            stores = False
            new_hw.set_custom_field("PII", "Yes")
            if "Transmits" in new_hw.get_custom_field("PHI") or "Transmits" in device['phi']:
                transmit = True
            if "Stores" in new_hw.get_custom_field("PHI") or "Stores" in device['phi']:
                stores = True
            if transmit and stores:
                new_hw.set_custom_field("PHI", "Transmits, Stores")
            elif transmit:
                new_hw.set_custom_field("PHI", "Transmits")
            elif stores:
                new_hw.set_custom_field("PHI", "Stores")

        # Add the new values to the old values
        new_hw.set_custom_field("Management", ', '.join(
            filter_list(new_hw.get_custom_field("Management").split(", ") + device['management_services'])))

        # Call clean_edr on the list
        device['endpoint_security_names'] = [clean_edr(edr) for edr in device['endpoint_security_names']]
        new_hw.set_custom_field("EDR", ', '.join(
            filter_list(new_hw.get_custom_field("EDR").split(", ") + device['endpoint_security_names'])))

        # If we still have an "Unknown" model, then improve the data (hopefully)
        if device['model'] and new_hw.model_id == DEFAULTS['model_id']:
            asset_config_auth['model_id'] = model.id

        last_user = clean_user(device['last_domain_user'])
        if last_user and last_user != new_hw.name:
            new_hw.set_custom_field("Last User", last_user)

        try:
            new_hw.upsert()
        except ValueError as e:
            logging.error(f"Error upserting {new_hw.name}: {e}")
