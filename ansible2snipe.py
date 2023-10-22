#!/usr/bin/env python3
# ansible2snipe - Inventory Import
#
# ABOUT:
#   This program is designed to import inventory information from an
#   Ansible Cache (currently MongoDB) into snipe-it using api calls. For more information
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
#   This setting sets the Snipe Asset status when creating a new asset. By default, it's set to 4 (Pending).
#   default_status = 4
#
#   You can associate Snipe-IT hardware keys in the [api-mapping] section, to an Ansible Cache key, so it associates
#   the jamf values into Snipe-IT. The default example associates information that exists by default in both
#   Snipe-IT and Ansible.  The Key value is the exact name of the Snipe-IT key name.
#   Note that MAC Address are a custom value in SNIPE by default, and you can use it as an example.
#
#   [api-mapping]
#       name = general name
#       _snipeit_mac_address_1 = ansible_mac_address
#       _snipeit_custom_name_1234567890 = ansible_dict ansible_key
#
import html
from functools import lru_cache
from time import sleep
from typing import Any, Iterable

from pymongo import MongoClient
import requests
from configparser import RawConfigParser
from argparse import ArgumentParser
import logging
from datetime import datetime
from jinja2 import Template
from pymongo.errors import PyMongoError

version = "0.1"
API_COUNT = 0
FIRST_API_CALL = None
MODELNUMBERS = {}
MANUFACTURERS = {}
DB: Any = None
SNIPE_RATE_LIMIT = 1000
CONFIG = {}


def request_handler(r, *args, **kwargs):
    # Implement rate limiting if username requests it
    global API_COUNT, USER_ARGS, FIRST_API_CALL
    if '"messages":429' in r.text:
        if USER_ARGS.ratelimited:
            logging.warning(
                "Despite respecting the rate limit of Snipe, we've still been limited. Trying again after sleeping for "
                "2 seconds.")
            sleep(2)
            re_req = r.request
            s = requests.Session()
            return s.send(re_req)

        logging.error(r.content)
        raise SystemExit(
            "We've been rate limited. Use option -r to sleep between requests to avoid this.")

    if not FIRST_API_CALL:
        FIRST_API_CALL = datetime.now()

    time_elapsed = datetime.now() - FIRST_API_CALL

    api_rate = 0
    if time_elapsed.seconds:
        api_rate = API_COUNT / time_elapsed.seconds

    max_rate = (SNIPE_RATE_LIMIT / 60) * .95
    API_COUNT += 1

    if USER_ARGS.ratelimited and api_rate > max_rate:
        sleep_time = 0.5 + (api_rate - max_rate)
        logging.debug(f'Rate limit {api_rate}/minute, sleeping for {sleep_time}')
        sleep(sleep_time)

    logging.debug(
        f"Made {API_COUNT} requests to Snipe IT in {time_elapsed} seconds, "
        f"with a request being sent at {api_rate}/second")

    return r


def do_mongo_query(query):
    try:
        cursor = DB.find(query)
    except PyMongoError as err:
        raise SystemExit("Error connecting to Ansible Cache: {}".format(err))
    return cursor


# Function to make the API call for all Ansible devices in an iterator
def get_ansible_computers(os):
    # Connect to MongoDB and get the data we need.
    logging.info("Getting a list of all {} computers.".format(os))
    return do_mongo_query({"data.ansible_system": os})


# Function to look up an Ansible asset by name.
def search_ansible_name(name):
    logging.info("Looking up name: {}".format(name))
    return do_mongo_query({"data.ansible_hostname": name})


# Function to look up a snipe asset by serial number.
def get_snipe_asset(serial):
    if not serial:
        return {"total": 0}
    api_url = f'hardware/byserial/{serial}'
    response = api_call(api_url)
    if 'total' not in response:
        response['total'] = 0

    return response


def api_call(endpoint, payload=None, method="GET"):
    global CONFIG, USER_ARGS
    # Headers for the API call.
    logging.info("Creating the headers we'll need for API calls")
    snipe_headers = {'Authorization': f"Bearer {CONFIG['snipe-it']['apikey']}",
                     'Accept': 'application/json',
                     'Content-Type': 'application/json'}
    logging.debug(f'Request headers for Snipe will be: {snipe_headers}')

    logging.debug(f"Calling {endpoint} with method {method} and payload {payload}")
    api_url = f"{CONFIG['snipe-it']['url']}/api/v1/{endpoint}"
    if method == "GET":
        logging.debug(f"Calling: {api_url}")
        response = requests.get(api_url, headers=snipe_headers, json=payload, verify=USER_ARGS.do_not_verify_ssl,
                                hooks={'response': request_handler})
    elif method == "POST":
        response = requests.post(api_url, headers=snipe_headers, json=payload, verify=USER_ARGS.do_not_verify_ssl,
                                 hooks={'response': request_handler})
    elif method == "PATCH":
        response = requests.patch(api_url, headers=snipe_headers, json=payload, verify=USER_ARGS.do_not_verify_ssl,
                                  hooks={'response': request_handler})
    else:
        logging.error(f"Unknown method {method}")
        raise SystemExit("Unknown method")

    if response.status_code != 200:
        logging.error(f"Snipe-IT responded with error code:{response.text}")
        logging.debug(f"{response.status_code} - {response.content}")
        raise SystemExit("Snipe-IT API call failed")
    logging.debug(f"Got a valid response from Snipe-IT: {response.text}")
    return response.json()


# Function to get all the asset models
@lru_cache(maxsize=None)
def get_snipe_models(page=0):
    page_size = 500
    limits = {
        'limit': page_size,
        'offset': page * page_size
    }
    models = {}
    response = api_call("models", payload=limits, method="GET")

    # This happens if there is an error
    if "total" not in response:
        logging.error("Fetching models failed, enable debug to see response")
        raise SystemExit("Necessary Snipe-IT API call failed")

    # Quickly end if there are no rows
    if "rows" not in response:
        return models

    # Add the models to the dictionary
    for row in response['rows']:
        models[row['model_number']] = row['id']
        models[row['name']] = row['id']

    # If we haven't gotten all the models, get more
    if response['total'] >= limits['offset']:
        logging.debug(f"Fetching more models, currently at: {limits['offset']}/{response['total']}")
        models.update(get_snipe_models(page + 1))

    return models


def get_snipe_model_id(model, manufacturer, device_type="computer"):
    global MODELNUMBERS, CONFIG
    if not MODELNUMBERS:
        MODELNUMBERS = get_snipe_models()

    if not clean_tag(model):
        logging.debug(f"Invalid model name {model} -> Unknown")
        return MODELNUMBERS['Unknown']

    if model in MODELNUMBERS:
        return MODELNUMBERS[model]

    logging.info(f"Could not find a model ID in snipe for: {model}")
    manufacturer_id = get_manufacturer(manufacturer)
    new_model = {
        "category_id": int(CONFIG['snipe-it'][f'{device_type}_category']),
        "manufacturer_id": manufacturer_id,
        "name": model,
        "model_number": model
    }
    if f'{device_type}_custom_fieldset_id' in CONFIG['snipe-it']:
        custom_fieldset = CONFIG['snipe-it'][f'{device_type}_custom_fieldset_id']
        new_model['fieldset_id'] = int(custom_fieldset)

    create_snipe_model(new_model)

    return MODELNUMBERS[model]


# Get user ID
@lru_cache(maxsize=None)
def get_snipe_user_id(username):
    if not username:
        return None

    payload = {"username": username, "all": True}
    response = api_call(f"users", payload=payload, method="GET")

    if 'total' not in response or response['total'] == 0:
        logging.debug(f"Got a valid response but no users")
        return None

    if response['total'] > 1:
        logging.warning(f"Got multiple responses for a username")
        return None

    return int(response['rows'][0]['id'])


# Function that creates a new Snipe Model - not an asset - with a JSON payload
def create_snipe_model(payload):
    global MODELNUMBERS
    response = api_call("models", payload, method="POST")
    MODELNUMBERS[response['payload']['model_number']] = int(response['payload']['id'])

    return MODELNUMBERS[response['payload']['model_number']]


# Function to create a new asset by passing array
def create_snipe_asset(payload):
    response = api_call("hardware", payload, method="POST")
    if response['status'] == "error":
        logging.error(f"Asset creation failed for asset {payload['name']} with error {response['messages']}")
        logging.error(f"{payload}")
        raise SystemExit("Asset creation failed")

    return response['payload']


# Function that updates a snipe asset with a JSON payload
def update_snipe_asset(snipe_id, payload):
    response = api_call(f'hardware/{snipe_id}', payload=payload, method="PATCH")
    if response['status'] == "error":
        logging.error(f"Asset update failed for asset {snipe_id} with error {response['messages']}")
        raise SystemExit("Asset update failed")

    return response['payload']


# Function that checks in an asset in snipe
def checkin_snipe_asset(asset_id):
    payload = {"note": "checked in by script from Ansible",
               "status_id": 2
               }
    return api_call(f'hardware/{asset_id}/checkin', method="POST", payload=payload)


def get_snipe_technicians():
    # TODO: Get this list from snipe (group based)
    global CONFIG
    if 'technicians' not in CONFIG['snipe-it']:
        return []
    return CONFIG['snipe-it']['technicians'].split(' ')


# Function that checks out an asset in snipe
def checkout_snipe_asset(username, asset):
    global USER_ARGS
    if not username:
        logging.debug("No username, not checking out asset")
        return False

    username = username.lower()
    # Remove domain if it exists
    if '\\' in username:
        username = username.split('\\')[1]
    if '@' in username:
        username = username.split('@')[0]

    if username in get_snipe_technicians():
        logging.debug(f"User {username} is a technician, not checking out asset")
        return True

    logging.info(f"User {username} is checking out {asset['id']}")

    user_id = get_snipe_user_id(username)
    if not user_id:
        logging.error(f"User {username} not found")
        return False

    if 'assigned_to' in asset and asset['assigned_to']:
        logging.info(f"Asset {asset['id']} is already checked out to {asset['assigned_to']}")

        if isinstance(asset['assigned_to'], int):
            if asset['assigned_to'] == user_id:
                return True
        elif 'id' in asset['assigned_to'] and asset['assigned_to']['id'] == user_id:
            return True

        if not USER_ARGS.users_force:
            logging.info("Not checking out asset, use users_force option to override")
            return False

        checkin_snipe_asset(asset['id'])

    payload = {
        "checkout_to_type": "user",
        "status_id": 2,
        "assigned_user": user_id
    }
    response = api_call(f'hardware/{asset["id"]}/checkout', payload=payload, method="POST")

    return response


def get_snipe_manufacturers():
    global MANUFACTURERS
    payload = {
        'limit': 500,
        'offset': len(MANUFACTURERS)
    }
    response = api_call("manufacturers", method="GET", payload=payload)

    for manufacturer in response['rows']:
        MANUFACTURERS[manufacturer['name']] = int(manufacturer['id'])

    if response['total'] > len(MANUFACTURERS):
        logging.debug(f"Total manufacturers is {response['total']} and we have {len(MANUFACTURERS)}")
        return get_snipe_manufacturers()

    return MANUFACTURERS


@lru_cache(maxsize=512)
def get_manufacturer(name: str) -> int:
    global MANUFACTURERS
    if not MANUFACTURERS:
        get_snipe_manufacturers()

    if not clean_tag(name):
        logging.debug(f"Skipping invalid manufacturer name {name}")
        return MANUFACTURERS['Unknown']

    if name in MANUFACTURERS:
        return MANUFACTURERS[name]

    logging.info(f"Creating manufacturer {name}")
    payload = {"name": name}
    response = api_call("manufacturers", payload=payload, method="POST")

    # If we do not have payload, but status 200, that means something went wrong
    if 'payload' not in response or not response['payload']:
        logging.error(f"Failed to create manufacturer {name}, response: {response}")
        raise SystemExit("Failed to create manufacturer")

    MANUFACTURERS[name] = int(response['payload']['id'])
    MANUFACTURERS[response['payload']['name']] = int(response['payload']['id'])

    return MANUFACTURERS[name]


def get_snipe_asset_by_name(name):
    payload = {
        'search': name,
        'limit': 50
    }
    response = api_call("hardware", method="GET", payload=payload)

    if 'rows' not in response:
        return {"total": 0}

    found = []
    # Search is fuzzy
    for row in response['rows']:
        if html.unescape(row['name'].upper()) == name.upper():
            found.append(row)

    response['rows'] = found
    response['total'] = len(found)
    return response


def get_snipe_asset_by_mac(mac_address):
    payload = {
        'search': mac_address,
        'limit': 50
    }
    response = api_call("hardware", method="GET", payload=payload)

    if 'rows' not in response:
        return {"total": 0}

    found = []
    # Search is fuzzy
    for row in response['rows']:
        for field_name in row['custom_fields']:
            field = row['custom_fields'][field_name]
            if 'mac_address' in field['field']:
                if field['value'].upper() == mac_address.upper():
                    found.append(row)
                    break

    if len(found) > 1:
        logging.warning(f"Found multiple assets with MAC {mac_address}")
        return SystemExit("Multiple assets found")

    response['rows'] = found
    response['total'] = len(found)
    return response


def get_os_config_value(os, config_key, data):
    value = get_config_value(CONFIG[f"{os}-api-mapping"][config_key], data)
    return clean_tag(value)


# Function to recursively get keys from a dictionary
def get_config_value(config_key, data, invalid_values=None):
    logging.debug(f"Getting config value for {config_key}")
    logging.debug(f"Data: {data}")
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
            logging.debug(f"Key value: {value}")
            value = None
            break

    if invalid_values and value in invalid_values:
        value = None

    if j2_str:
        template = Template(j2_str)
        value = template.render(var=value, data=data)

    logging.debug(f"Got value {value} for {config_key}")
    return value


def clean_mac(mac_address: str) -> str | None:
    if mac_address.startswith('0A:00:27'):
        return None
    return mac_address


def clean_os(operating_system: str) -> str:
    if operating_system == 'Red Hat':
        return "RedHat"
    if "Monterey" in operating_system:
        return "macOS"
    if operating_system.startswith("Mac OS 10"):
        return "Mac OS X"
    return operating_system


def clean_tag(value: Any) -> str | None:
    invalid = ["na",
               "not available",
               "to be filled by o.e.m.",
               "to be filled by o.e.m",
               "to be filled by oem",
               "system serial number",
               "0123456789",
               "1234567890",
               "default string",
               "no asset tag",
               "asset tag",
               "not specified",
               "system manufacturer",
               "0",
               "system product name",
               "null",
               "none",
               "main board",
               "0000000000",
               "7783-7084-3265-9085-8269-3286-77",
               "no asset information",
               "tangent197",
               "isd_pcs",
               "cbx3__",
               "chassis serial number"
               "123-1234-123",
               "..................",
               "empty"]

    if not value or len(str(value)) < 3 or str(value).lower() in invalid:
        return None

    logging.debug(f"Clean tag: {value}")
    return str(value)


def clean_manufacturer(manufacturer):
    if not manufacturer:
        logging.info(f"Manufacturer not available. Setting to Unknown.")
        return 'Unknown'

    manufacturer_lower = manufacturer.lower()
    if manufacturer_lower.startswith('apple'):
        return 'Apple'
    elif manufacturer_lower.startswith('dell') or manufacturer_lower.endswith('ell inc.'):
        return 'Dell Inc.'
    elif manufacturer_lower.startswith('aaeon'):
        return 'AAEON Technology Inc.'
    elif manufacturer_lower.startswith('asix'):
        return 'ASIX Electronics Corporation'
    elif manufacturer_lower.startswith('advansus'):
        return 'Advansus Corp.'
    elif manufacturer_lower.startswith('advantech'):
        return 'Advantech Co., Ltd.'
    elif manufacturer_lower.startswith('andover'):
        return 'Andover Controls Corporation'
    elif manufacturer_lower.startswith('armorlin'):
        return 'Armorlink Co., Ltd.'
    elif manufacturer_lower.startswith('asrock'):
        return 'ASRock Incorporation'
    elif manufacturer_lower.startswith('axiom'):
        return 'Axiom Technology Co., Ltd.'
    elif manufacturer_lower.startswith('asus'):
        return 'ASUSTeK Computer Inc.'
    elif manufacturer_lower.startswith('azurewav'):
        return 'AzureWave Technologies, Inc.'
    elif manufacturer_lower.startswith('belkin'):
        return 'Belkin International Inc.'
    elif manufacturer_lower.startswith('bizlink'):
        return 'BizLink (Kunshan) Co.,Ltd'
    elif manufacturer_lower.startswith('brady'):
        return 'Brady Corporation'
    elif manufacturer_lower.startswith('broadcom'):
        return 'Broadcom Inc.'
    elif manufacturer_lower.startswith('ce') and 'link' in manufacturer_lower:
        return 'Ce Link Limited'
    elif manufacturer_lower.startswith('chongqin'):
        return 'Chongqing Fugui Electronics Co.,Ltd.'
    elif manufacturer_lower.startswith('cisco'):
        return 'Cisco Systems, Inc.'
    elif manufacturer_lower.startswith('cloud') and 'net' in manufacturer_lower:
        return 'Cloud Network Technology (Samoa) Limited'
    elif manufacturer_lower.startswith('cyberpow'):
        return 'Cyber Power Systems, Inc.'
    elif manufacturer_lower.startswith('cybernet'):
        return 'Cybernet Manufacturing Inc.'
    elif manufacturer_lower.startswith('dfi'):
        return 'DFI Inc.'
    elif manufacturer_lower.startswith('flytech'):
        return 'Flytech Technology Co., Ltd.'
    elif manufacturer_lower.startswith('fujitsu'):
        return 'Fujitsu'
    elif manufacturer_lower.startswith('gigabyte') or manufacturer_lower.startswith('giga-byte'):
        return 'Gigabyte Technology Co., Ltd.'
    elif manufacturer_lower.startswith('gigamon'):
        return 'Gigamon Systems LLC'
    elif manufacturer_lower.startswith('good') and 'way' in manufacturer_lower:
        return 'Good Way Technology Co., Ltd.'
    # Do HPE before HP
    elif (manufacturer_lower.startswith('hpe') or
          ('hewlett' in manufacturer_lower and 'enterprise' in manufacturer_lower)):
        return "Hewlett Packard Enterprise"
    elif manufacturer_lower.startswith('hp') or manufacturer_lower.startswith('hewlett'):
        return 'Hewlett-Packard'
    elif manufacturer_lower.startswith('hitachi'):
        return 'Hitachi'
    elif manufacturer_lower.startswith('huizhou') and 'd' in manufacturer_lower:
        return 'Huizhou Dehong Technology Co., Ltd.'
    elif manufacturer_lower.startswith('hon') and 'hai' in manufacturer_lower:
        return 'Hon Hai Precision Ind. Co.,Ltd.'
    elif manufacturer_lower.startswith('intel'):
        return 'Intel Corporation'
    elif manufacturer_lower.startswith('ibm'):
        return 'IBM'
    elif manufacturer_lower.startswith('juniper'):
        return 'Juniper'
    elif manufacturer_lower.startswith('jump') and 'indu' in manufacturer_lower:
        return 'JUMPtec Industrielle Computertechnik AG'
    elif manufacturer_lower.startswith('jetway') and 'in' in manufacturer_lower:
        return 'Jetway Information Co., Ltd.'
    elif manufacturer_lower.startswith('kcodes'):
        return 'KCodes Corporation'
    elif manufacturer_lower.startswith('lcfc'):
        return 'LCFC(HeFei) Electronics Technology Co., Ltd.'
    elif manufacturer_lower.startswith('lenovo'):
        return 'Lenovo'
    elif manufacturer_lower.startswith('luxshare'):
        return 'Luxshare Precision Industry Co., Ltd.'
    elif manufacturer_lower.startswith('liteon'):
        return 'Liteon Technology Corporation'
    elif manufacturer_lower.startswith('lg'):
        return 'LG Electronics'
    elif manufacturer_lower.startswith('micro-star'):
        return 'Micro-Star International Co., Ltd.'
    elif manufacturer_lower.startswith('microsof'):
        return 'Microsoft Corporation'
    elif manufacturer_lower.startswith('mitac'):
        return 'Mitac International Corp.'
    elif manufacturer_lower.startswith('nec'):
        return 'NEC Corporation'
    elif manufacturer_lower.startswith('oracle'):
        return 'Oracle Corporation'
    elif manufacturer_lower.startswith('parallels'):
        return 'Parallels Software International Inc.'
    elif manufacturer_lower.startswith('pc') and 'partne' in manufacturer_lower:
        return 'PC Partner Ltd.'
    elif manufacturer_lower.startswith('palo alto'):
        return 'Palo Alto Networks'
    elif manufacturer_lower.startswith('panasonic'):
        return 'Panasonic'
    elif manufacturer_lower.startswith('pioneer'):
        return 'Pioneer'
    elif manufacturer_lower.startswith('realtek'):
        return 'Realtek Semiconductor Corp.'
    elif 'schneider electric' in manufacturer_lower:
        return 'Schneider Electric'
    elif manufacturer_lower.startswith('siemens'):
        return 'Siemens AG'
    elif manufacturer_lower.startswith('summit'):
        return 'Summit Data Communications'
    elif manufacturer_lower.startswith('sony'):
        return 'Sony Corporation'
    elif manufacturer_lower.startswith('super') and 'micro' in manufacturer_lower:
        return 'Super Micro Computer, Inc.'
    elif manufacturer_lower.startswith('tangent'):
        return 'Tangent, Inc.'
    elif manufacturer_lower.startswith('toshiba'):
        return 'Toshiba Corporation'
    elif manufacturer_lower.startswith('texas') and 'ins' in manufacturer_lower:
        return 'Texas Instruments'
    elif manufacturer_lower.startswith('tyan'):
        return 'Tyan Computer Corp.'
    elif manufacturer_lower.startswith('vmware'):
        return 'VMware, Inc.'
    elif manufacturer_lower.startswith('variscit'):
        return 'Variscite LTD'
    elif manufacturer_lower.startswith('wistron'):
        return 'Wistron Corporation'
    elif manufacturer_lower.startswith('zebra'):
        return 'Zebra Technologies Inc.'
    elif manufacturer_lower.startswith('congatec'):
        return 'congatec AG'
    elif manufacturer_lower.startswith('3s') and ('system' in manufacturer_lower or 'vision' in manufacturer_lower):
        return '3S System Tech Inc.'
    elif manufacturer_lower.startswith('speed') and 'dra' in manufacturer_lower:
        return 'Speed Dragon Multimedia Limited'

    return manufacturer


def extract_api_mapping(os: str, asset_data: Iterable) -> dict:
    global CONFIG
    return_dict = {}
    for snipekey in CONFIG[f"{os}-api-mapping"]:
        if not snipekey.startswith("_snipeit_"):
            continue

        value = get_os_config_value(os, snipekey, asset_data)
        if value:
            logging.debug(f"Setting {snipekey} to {value}")
            return_dict[snipekey] = value

    return return_dict


# Always run this
# Set us up for using runtime arguments by defining them.
runtime_args = ArgumentParser()
runtime_args.add_argument("-v", "--verbose",
                          help="Sets the logging level to INFO, which will print out more information.",
                          action="store_true")
runtime_args.add_argument("--auto_incrementing",
                          help="If you have auto-incrementing enabled in your snipe instance, utilize that",
                          action="store_true")
runtime_args.add_argument("--dryrun",
                          help="This checks your CONFIG but exits before making any changes to Snipe-IT.",
                          action="store_true")
runtime_args.add_argument("-d", "--debug", help="Sets logging to include additional DEBUG messages.",
                          action="store_true")
runtime_args.add_argument('--do_not_verify_ssl',
                          help="Skips SSL verification for all requests.",
                          action="store_false")
runtime_args.add_argument("-r", "--ratelimited",
                          help="Enable rate-limiting (recommended)"
                               "limit",
                          action="store_true")
runtime_args.add_argument("-f", "--force",
                          help="Update the Snipe asset with information from Ansible Cache every time even if "
                               "Snipe-IT has a newer record",
                          action="store_true")
runtime_args.add_argument("--version", help="Prints the version and exits.", action="store_true")
user_opts = runtime_args.add_mutually_exclusive_group()
user_opts.add_argument("-u", "--users",
                       help="Checks out the asset to the current username in Ansible if it's not assigned",
                       action="store_true")
user_opts.add_argument("-uf", "--users_force",
                       help="Checks out the asset to the current username in Ansible even if it is assigned",
                       action="store_true")
USER_ARGS = runtime_args.parse_args()

if USER_ARGS.version:
    print(version)
    raise SystemExit

if USER_ARGS.debug:
    logging.basicConfig(level=logging.DEBUG)
elif USER_ARGS.verbose:
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.WARNING)

# Notify users if we're doing a dry run.
if USER_ARGS.dryrun:
    print("Dryrun: Starting ansible2snipe with a dry run where no assets will be updated.")

# Find a valid settings.conf file.
logging.info("Searching for a valid settings.conf file.")
CONFIG = RawConfigParser()
logging.debug("Checking for a settings.conf in /opt/jamf2snipe ...")
CONFIG.read("/opt/ansible2snipe/settings.conf")
if 'snipe-it' not in set(CONFIG):
    logging.debug("No valid CONFIG found in: /opt Checking for a settings.conf in /etc/jamf2snipe ...")
    CONFIG.read('/etc/jamf2snipe/settings.conf')
if 'snipe-it' not in set(CONFIG):
    logging.debug("No valid CONFIG found in /etc Checking for a settings.conf in current directory ...")
    CONFIG.read("settings.conf")
if 'snipe-it' not in set(CONFIG):
    logging.debug("No valid CONFIG found in current folder.")
    logging.error(
        "No valid settings.conf was found. We'll need to quit while you figure out where the settings are at. "
        "You can check the README for valid locations.")
    raise SystemExit("Error: No valid settings.conf - Exiting.")

logging.info("Great, we found a settings file. Let's get started by parsing all of the settings.")

# While setting the variables, use a try loop so, we can raise an error if something goes wrong.
try:
    logging.info("Setting the base URL for SnipeIT.")
    logging.debug(f"The configured Snipe-IT base url is: {CONFIG['snipe-it']['url']}")

    logging.info("Setting the API key for SnipeIT.")
    logging.debug(f"The API key you provided for Snipe is: {CONFIG['snipe-it']['apikey']}")

    logging.info("Getting the OS types we'll be looking for.")
    os_types = CONFIG['ansible']['os'].split(',')
except KeyError:
    logging.error(
        "Some of the required settings from the settings.conf were missing or invalid. "
        "Re-run ansible2snipe with the --verbose or --debug flag to get more details.")
    raise SystemExit("Error: Missing or invalid settings in settings.conf - Exiting.")

# Check the CONFIG file for correct headers

# Do some tests to see if the admin has updated their settings.conf file
settings_correct = True
if CONFIG['snipe-it']['url'].endswith("/"):
    logging.error("""You have a trailing forward slash in the Snipe-IT url. Please remove it.""")
    settings_correct = False

if not settings_correct:
    raise SystemExit

# Run Testing
# Report if we're verifying SSL or not.
logging.info("SSL Verification is set to: {}".format(USER_ARGS.do_not_verify_ssl))


def main():
    global API_COUNT, DB, CONFIG

    # Do some tests to see if the hosts are up. Don't use hooks for these as we don't have tokens yet.
    logging.info("Running tests to see if hosts are up.")

    response = api_call("ping", method="GET")
    if not response.text:
        logging.error('Snipe-IT looks like it is down from here. \n'
                      'Please check your CONFIG in the settings.conf file, or your instance.')
        raise SystemExit("Error: Host could not be contacted.")

    logging.info('We were able to get a good response from your Snipe-IT instance.')

    try:
        ansible_base = CONFIG['ansible']['url']
        DB = MongoClient(ansible_base)["ansible"]["cache"]
    except KeyError:
        logging.error("Missing key(s) in ansible section. Please check your settings.conf file")
        raise SystemExit("Error: Missing or invalid settings in settings.conf - Exiting.")
    except PyMongoError as err:
        logging.error(f"Error connecting to Ansible Cache: {err}")
        raise SystemExit("Error: Could not connect to Ansible Cache - Exiting.")

    # After this point we start editing data, so quit if this is a dryrun
    if USER_ARGS.dryrun:
        raise SystemExit("Dryrun: Complete.")

    # From this point on, we're editing data.
    logging.info('Starting to Update Inventory')

    for os in os_types:
        logging.info(f"Starting to update {os} inventory.")
        # Get category
        if f"{os}-api-mapping" not in CONFIG:
            logging.error(f"No api-mapping section found for {os}")
            raise SystemExit("Error: Missing or invalid settings in settings.conf - Exiting.")

        try:
            device_type = CONFIG[f"{os}-api-mapping"]['device_type']
            default_category = int(CONFIG['snipe-it'][f'{device_type}_category'])
            default_status = int(CONFIG['snipe-it'][f'{device_type}_status'])
        except (KeyError, ValueError):
            logging.error(f"Missing key(s) in {os}-api-mapping section. Please check your settings.conf file")
            raise SystemExit("Error: Missing or invalid settings in settings.conf - Exiting.")

        for ansible_asset in get_ansible_computers(os):
            if not ansible_asset:
                continue
            # If the entry doesn't contain a serial or asset id, then we need to skip this entry.
            computer_name = ansible_asset['_id']
            logging.debug(f"The asset we're working on is: {computer_name}")

            serial = get_os_config_value(os, 'serial', ansible_asset['data'])
            asset_tag = get_os_config_value(os, 'asset_tag', ansible_asset['data'])
            model = get_os_config_value(os, 'model', ansible_asset['data'])
            manufacturer = clean_manufacturer(get_os_config_value(os, 'manufacturer', ansible_asset['data']))

            snipe_asset = get_snipe_asset(serial)
            if snipe_asset['total'] == 0:
                logging.info(f"Serial number {serial} not found in snipe. Checking for asset name.")
                snipe_asset = get_snipe_asset_by_name(computer_name)

            if not serial:
                logging.debug(f"Serial number not found for {ansible_asset['_id']}. Skipping.")
                serial = f"ans-{ansible_asset['_id']}"

            if not asset_tag:
                logging.debug(f"Asset tag not found for {ansible_asset['_id']}. Skipping.")
                asset_tag = f"ans-{ansible_asset['_id']}"

            logging.debug(f"Snipe returned: {snipe_asset}")
            if snipe_asset['total'] > 1:
                logging.warning(f"Multiple assets found for {serial}. Skipping.")
                continue

            if not model:
                logging.info(f"Model not available for {ansible_asset['_id']}. Setting to Unknown.")
                model = "Unknown"
                # Manufacturer is a dependency of model, so if model is unknown, manufacturer is unknown
                manufacturer = "Unknown"

            model_id = get_snipe_model_id(model, manufacturer, device_type)

            # Create a payload:
            payload = {
                "name": ansible_asset['_id'],
                "serial": serial,
                "status_id": default_status,
                "category_id": default_category,
                "model_id": model_id
            }

            if not USER_ARGS.auto_incrementing:
                payload['asset_tag'] = asset_tag

            extra_data = extract_api_mapping(os, ansible_asset['data'])
            payload.update(extra_data)

            asset = {}
            if not snipe_asset['total']:
                logging.info(f"Creating a new asset in snipe for {ansible_asset['_id']}")
                logging.debug(f"Creating new asset with payload: {payload}")
                asset = create_snipe_asset(payload)

            if snipe_asset['total'] == 1:
                logging.info(f"Existing asset in Snipe-IT for {ansible_asset['_id']}")
                asset = snipe_asset['rows'][0]
                update_time = asset['updated_at']['datetime']
                # Convert to datetime object
                update_time = datetime.strptime(update_time, '%Y-%m-%d %H:%M:%S')
                # Convert asset['date'] to datetime object (if driver not MongoDB)
                if isinstance(ansible_asset['date'], str):
                    ansible_asset['date'] = datetime.strptime(ansible_asset['date'], '%Y-%m-%dT%H:%M:%S.%f%z')
                # Compare update_time to ansible update time
                if update_time >= ansible_asset['date'] and not USER_ARGS.force:
                    logging.info(f"Skipping update for {ansible_asset['_id']} because the Snipe record is newer.")
                    continue

                if payload['serial'] == asset['serial'] or payload['serial'].startswith('ans-'):
                    del payload['serial']

                if payload['asset_tag'] == asset['asset_tag'] or payload['asset_tag'].startswith('ans-'):
                    del payload['asset_tag']

                for key in asset:
                    if key in payload and str(asset[key]) == str(payload[key]):
                        del payload[key]

                if payload['model_id'] == asset['model']['id']:
                    del payload['model_id']
                if payload['status_id'] == asset['status_label']['id']:
                    del payload['status_id']
                if payload['category_id'] == asset['category']['id']:
                    del payload['category_id']

                for key, value in asset['custom_fields'].items():
                    if value['field'] in payload and str(payload[value['field']]) == str(value['value']):
                        del payload[value['field']]

                if payload:
                    update_snipe_asset(asset['id'], payload)

                logging.debug(f"Done updating {ansible_asset['_id']}")

            # Check if we need to check out the asset
            if USER_ARGS.users or USER_ARGS.users_force:
                username = get_os_config_value(os, 'user_field', ansible_asset['data'])
                logging.debug(f"User is {username}")
                checkout_snipe_asset(username, asset)

                # If there is no username, it is possible the username is logged out, make no changes

    logging.debug('Total amount of API calls made: {}'.format(API_COUNT))


if __name__ == "__main__":
    main()
