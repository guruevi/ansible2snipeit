#!/usr/bin/env python3
import logging
from configparser import RawConfigParser
from snipeit_api.api import SnipeITApi
from snipeit_api.helpers import get_dept_from_ou, get_lab_from_ou
from snipeit_api.models import Hardware


def main():
    config = RawConfigParser()
    logging.basicConfig(level=logging.INFO)

    logging.debug("Checking for a settings.conf ...")
    config.read("settings.conf")
    snipeit_apiurl = config.get('snipe-it', 'url')
    snipeit_apikey = config.get('snipe-it', 'apikey')
    snipeapi = SnipeITApi(snipeit_apiurl, snipeit_apikey)
    offset = 0
    limit = 300
    total = 0
    missing_ou = set()
    while offset <= total:
        pages = snipeapi.call(f'hardware?limit={limit}&offset={offset}', method='GET')
        offset += limit

        total = pages['total']
        for asset in pages['rows']:
            ou = asset['custom_fields']['Org. Unit']['value']
            if not ou:
                continue
            dept_name = get_dept_from_ou(ou)
            lab_name = get_lab_from_ou(ou)
            if not dept_name:
                missing_ou.add(ou)
            if (asset['custom_fields']['Department']['value'] != dept_name or
                    lab_name != asset['custom_fields']['Lab']['value']):
                snipe_obj = Hardware(api=snipeapi).get_by_id(asset['id'])
                (snipe_obj.get_by_id()
                 .store_state()
                 .set_custom_field('Department', dept_name)
                 .set_custom_field('Lab', lab_name))
                snipe_obj.upsert()
                logging.info(f"Updating {asset['name']}")

    logging.info(f"Missing OUs:")
    for ou in missing_ou:
        logging.info(ou)


if __name__ == "__main__":
    main()
