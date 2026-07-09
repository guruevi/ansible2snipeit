#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Search SnipeIT for disabled devices
import logging
from configparser import RawConfigParser
from time import sleep

from snipeit_api.api import SnipeITApi
from snipeit_api.models import Hardware

logging.basicConfig(level=logging.INFO)
CONFIG = RawConfigParser()
logging.debug("Checking for a settings.conf ...")
CONFIG.read("settings.conf")
snipeit_apiurl = CONFIG.get('snipe-it', 'url')
snipeit_apikey = CONFIG.get('snipe-it', 'apikey')

snipe_api = SnipeITApi(url=snipeit_apiurl, api_key=snipeit_apikey)

page = 0
while True:
    data = snipe_api.call('hardware', {'search': 'disabled', 'limit': 500})
    if not data or 'rows' not in data or not data['rows']:
        break
    for result in data['rows']:
        obj = snipe_api.call(f"hardware/{result['id']}/checkin", method='POST', payload={'status_id': 3})
        if obj['status'] == 'success':
            logging.info(f"Checked in {result['name']}")
        else:
            snipe_api.call(f"hardware/{result['id']}", method='PATCH', payload={'status_id': 3})
    sleep(10)