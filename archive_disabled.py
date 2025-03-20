#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Search SnipeIT for disabled devices
import logging
from configparser import RawConfigParser

from snipeit_api.api import SnipeITApi
from snipeit_api.models import Hardware

logging.basicConfig(level=logging.INFO)
CONFIG = RawConfigParser()
logging.debug("Checking for a settings.conf ...")
CONFIG.read("settings.conf")
snipeit_apiurl = CONFIG.get('snipe-it', 'url')
snipeit_apikey = CONFIG.get('snipe-it', 'apikey')

snipe_api = SnipeITApi(url=snipeit_apiurl, api_key=snipeit_apikey)

data = snipe_api.call('hardware', {'search': 'disabled computer'})
for result in data['rows']:
    snipe_api.call(f"hardware/{result['id']}/checkin", method='POST', payload={'status_id': 3})