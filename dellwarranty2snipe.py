#!/usr/bin/env python3
from datetime import datetime
from requests.exceptions import JSONDecodeError
from dell_api.__main__ import DellApi

dell_api = DellApi()

from ansible2snipe import api_call

dell_manufacturer_id = 2
offset = 0
limit = 99
total = 0
page = f'hardware?limit={limit}&manufacturer_id={dell_manufacturer_id}'

while offset <= total:
    pages = api_call(f'{page}&offset={offset}', method='GET')
    offset += limit

    total = pages['total']
    serials = {}
    for asset in pages['rows']:
        serial = asset['serial'].lower()
        if serial.startswith('sccm-') or serial.startswith('ordr-') or serial.startswith('ans-'):
            continue
        if asset['purchase_date']:
            continue
        serials[asset['serial']] = asset['id']

    if not serials:
        continue

    try:
        warranties = dell_api.asset_warranty(list(serials.keys()))
    except JSONDecodeError:
        print(f"Invalid key in {serials.keys()}")
        continue

    for warranty in warranties:
        payload = {}
        # We need to find purchase_date
        # We need to find warranty_months
        url = f'hardware/{serials[warranty["serviceTag"]]}'
        if 'shipDate' not in warranty or not warranty['shipDate']:
            continue

        try:
            shipDate = datetime.strptime(warranty['shipDate'], '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            shipDate = datetime.strptime(warranty['shipDate'], '%Y-%m-%dT%H:%M:%S.%fZ')

        payload['purchase_date'] = shipDate.strftime('%Y-%m-%d')
        payload['warranty_months'] = 0
        # Parse shipDate to datetime object

        if 'entitlements' not in warranty:
            continue

        for entitlement in warranty['entitlements']:
            print(entitlement)
            if 'endDate' not in entitlement or not entitlement['endDate']:
                continue
            # Parse endDate to datetime object
            try:
                endDate = datetime.strptime(entitlement['endDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                endDate = datetime.strptime(entitlement['endDate'], '%Y-%m-%dT%H:%M:%SZ')
            # Calculate warranty_months
            warranty_months = (endDate.year - shipDate.year) * 12 + (endDate.month - shipDate.month)
            if warranty_months > payload['warranty_months']:
                payload['warranty_months'] = warranty_months

        if payload:
            api_call(f"hardware/{serials[warranty['serviceTag']]}", method='PATCH', payload=payload)
