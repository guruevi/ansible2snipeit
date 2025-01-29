#!/usr/bin/env python3
import logging
from configparser import RawConfigParser
from copy import deepcopy

from tenable.sc import TenableSC
from snipeit_api.api import SnipeITApi
from snipeit_api.defaults import DEFAULTS
from snipeit_api.helpers import filter_list
from snipeit_api.models import Hardware


def main():
    config = RawConfigParser()
    logging.basicConfig(level=logging.ERROR)
    logging.debug("Checking for a settings.conf ...")
    config.read("settings.conf")
    snipeit_apiurl = config.get('snipe-it', 'url')
    snipeit_apikey = config.get('snipe-it', 'apikey')
    snipe_api = SnipeITApi(snipeit_apiurl, snipeit_apikey)
    tenable_url = config.get('tenable', 'url')
    username = config.get('tenable', 'username')
    password = config.get('tenable', 'password')

    sc = TenableSC(tenable_url)
    sc.login(username, password)

    # Authenticated Scans
    query = ('pluginID', '=', '110095,22869,20811,178102')
    vulnerable_hosts = sc.analysis.vulns(query)

    # Make a unique list of hostnames and MAC addresses
    for host in vulnerable_hosts:
        shortname = host['dnsName'].split('.')[0].upper()
        if not host['macAddress'] and not shortname:
            logging.error(f"Cannot uniquely identify {host['ip']} - {host['dnsName']}")
            continue
        new_hw: Hardware = (Hardware(api=snipe_api, custom_fields=deepcopy(DEFAULTS['custom_fields']))
                            .get_by_mac([host['macAddress']])
                            .get_by_name(shortname)
                            .store_state())
        if not new_hw.id:
            logging.error(f"Cannot find {shortname} - {host['macAddress']}")
            continue
        current_edr = new_hw.get_custom_field('EDR').split(", ")
        new_hw.set_custom_field('EDR', ", ".join(filter_list(current_edr + ["Tenable Nessus"])))
        new_hw.set_custom_field('IP Address', host['ip'])
        new_hw.upsert()


if __name__ == "__main__":
    main()
