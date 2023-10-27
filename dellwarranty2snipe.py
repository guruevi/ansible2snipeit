#!/usr/bin/env python3
from datetime import datetime

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

    warranties = dell_api.asset_warranty(list(serials.keys()))
    for warranty in warranties:
        payload = {}
        # We need to find purchase_date
        # We need to find warranty_months
        # {'id': 2077717341, 'serviceTag': '8B3Y4Y3', 'orderBuid': 11, 'shipDate': '2023-10-09T05:00:00Z', 'productCode': '>/226', 'localChannel': '84', 'productId': None, 'productLineDescription': 'LATITUDE 5540', 'productFamily': None, 'systemDescription': None, 'productLobDescription': 'Latitude', 'countryCode': 'US', 'duplicated': False, 'invalid': False, 'entitlements': [{'itemNumber': '812-3888', 'startDate': '2023-10-09T05:00:00Z', 'endDate': '2027-01-07T05:59:59.000001Z', 'entitlementType': 'INITIAL', 'serviceLevelCode': 'ND', 'serviceLevelDescription': 'Onsite Service After Remote Diagnosis (Consumer Customer)/ Next Business Day Onsite After Remote Diagnosis (for business Customer)', 'serviceLevelGroup': 5}]}
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

