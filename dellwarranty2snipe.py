#!/usr/bin/env python3
import logging
from configparser import RawConfigParser
from datetime import datetime
from dell_api.__main__ import DellApi
from requests.exceptions import JSONDecodeError
from snipeit_api.api import SnipeITApi
from snipeit_api.defaults import DEFAULTS
from snipeit_api.helpers import clean_tag
from snipeit_api.models import Manufacturers, Models


# Give it a list of Dell serials
# It will return a dict with { "serial": { "purchase_date": "YYYY-MM-DD", "warranty_months": 12 } }
def get_dell_warranty(serials: list, manufacturer_id: int, snipeapi: SnipeITApi, api: DellApi|None = None) \
        -> dict[str, dict]:
    if not api:
        api = DellApi()

    try:
        dell_warranties = api.asset_warranty(serials)
    except JSONDecodeError:
        logging.error(f"Invalid key/serial in serial")
        logging.debug(serials)
        return {}

    info = {}
    for dell_warranty in dell_warranties:
        logging.debug(dell_warranty)
        # We need to find purchase_date
        # We need to find warranty_months
        if 'shipDate' not in dell_warranty or not dell_warranty['shipDate']:
            continue

        try:
            ship_date = datetime.strptime(dell_warranty['shipDate'], '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            try:
                ship_date = datetime.strptime(dell_warranty['shipDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                logging.error(f"Invalid shipDate {dell_warranty['shipDate']}")
                continue

        if 'entitlements' not in dell_warranty or not dell_warranty['entitlements']:
            dell_warranty['entitlements'] = {}

        info[dell_warranty['serviceTag']] = {}
        model_name = dell_warranty['productLineDescription'].replace("Dell System ", "").replace("Dell ", "").title()
        if clean_tag(model_name):
            model = (Models(api=snipeapi, name=model_name)
                     .get_by_name()
                     .populate({"name": model_name,
                                "model_number": dell_warranty['productCode'].upper(),
                                "manufacturer_id": manufacturer_id,
                                "category_id": DEFAULTS['category_id'],
                                "fieldset_id": DEFAULTS['fieldset_id'],
                                "eol": 60
                                })
                     .create())
            info[dell_warranty['serviceTag']]['model_id'] = model.id
        # Parse shipDate to datetime object
        info[dell_warranty['serviceTag']]['purchase_date'] = ship_date.strftime('%Y-%m-%d')
        info[dell_warranty['serviceTag']]['warranty_months'] = 12  # This is the standard warranty

        for entitlement in dell_warranty['entitlements']:
            logging.debug(entitlement)
            if 'endDate' not in entitlement or not entitlement['endDate']:
                continue
            # Parse endDate to datetime object
            try:
                end_date = datetime.strptime(entitlement['endDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                end_date = datetime.strptime(entitlement['endDate'], '%Y-%m-%dT%H:%M:%SZ')
            # Calculate warranty_months
            warranty_months = (end_date.year - ship_date.year) * 12 + (end_date.month - ship_date.month)
            if warranty_months > info[dell_warranty['serviceTag']]['warranty_months']:
                info[dell_warranty['serviceTag']]['warranty_months'] = warranty_months

    return info


def main():
    dell_api = DellApi()
    logging.basicConfig(level=logging.ERROR)

    config = RawConfigParser()
    config.read("settings.conf")
    snipeit_apiurl = config.get('snipe-it', 'url')
    snipeit_apikey = config.get('snipe-it', 'apikey')
    snipeapi = SnipeITApi(snipeit_apiurl, snipeit_apikey)

    dell_manufacturer = Manufacturers(api=snipeapi).get_by_name("Dell")
    alienware_manufacturer = Manufacturers(api=snipeapi).get_by_name("Alienware")
    unknown_manufacturer = Manufacturers(api=snipeapi).get_by_name("Unknown")

    for manufacturer in [unknown_manufacturer, dell_manufacturer, alienware_manufacturer]:
        offset = 0
        limit = 99  # Limit on the Dell API
        total = 0
        page = f'hardware?limit={limit}&manufacturer_id={manufacturer.id}'
        while offset <= total:
            pages = snipeapi.call(f"{page}&offset={offset}", method='GET')
            offset += limit

            total = pages['total']
            # Serials_id is a dict with { "serial": "snipeid" }
            serials_id = {}
            for asset in pages['rows']:
                serial = asset['serial'].lower()
                if len(serial) != 7:
                    logging.warning(f"Invalid serial {serial} in {asset['name']}")
                    continue
                if asset['purchase_date']:
                    continue
                serials_id[asset['serial']] = asset['id']

            if not serials_id:
                continue

            warranties = get_dell_warranty(serials=list(serials_id.keys()),
                                           manufacturer_id=dell_manufacturer.id,
                                           api=dell_api,
                                           snipeapi=snipeapi)
            logging.debug(warranties)
            for serial, warranty in warranties.items():
                snipeapi.call(f"hardware/{serials_id[serial]}", method='PATCH', payload=warranty)


if __name__ == "__main__":
    main()
