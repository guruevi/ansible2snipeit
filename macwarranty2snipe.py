#!/usr/bin/env python3
import re
import datetime

from ansible2snipe import snipe_api_call

YEAR_REGEXP = re.compile(r'\d{4}')


def query_apple_warranty(serial, model_name=None):
    # http://www.macrumors.com/2010/04/16/apple-tweaks-serial-number-format-with-new-macbook-pro/

    year_re = YEAR_REGEXP.search(model_name)
    if not year_re:
        print(f"No year found in model name {model_name}, skipping {serial}")
        return None
    year = int(year_re.group())

    if len(serial) == 11:
        # Old format
        year = serial[2].lower()
        est_year = 2000 + '   3456789012'.index(year)
        week = int(serial[3:5]) - 1
        year_time = datetime.date(year=int(est_year), month=1, day=1)
        if week:
            week_dif = datetime.timedelta(weeks=int(week))
            year_time += week_dif

        return year_time
    # Apple starts randomizing serial numbers in 2021
    elif year < 2021 and 11 < len(serial) < 16:
        # New format
        alpha_year = 'cdfghjklmnpqrstvwxyz'
        alpha_est_year = serial[3].lower()
        est_year = int(2010 + (alpha_year.index(alpha_est_year) / 2))
        # 1st or 2nd half of the year
        est_half = alpha_year.index(alpha_est_year) % 2
        week = serial[4].lower()
        alpha_week = ' 123456789cdfghjklmnpqrtvwxy'
        est_week = alpha_week.index(week) + (est_half * 26) - 1
        # If the year is off by more than 3 years, assume we're miscalculating
        if abs(year - est_year) > 3:
            est_year += 10
        year_time = datetime.date(year=est_year, month=1, day=1)
        if est_week:
            week_dif = datetime.timedelta(weeks=int(est_week))
            year_time += week_dif
        return year_time

    return datetime.date(year=year, month=1, day=1)


apple_manufacturer_id = 1
offset = 0
limit = 99
total = 0
page = f'hardware?limit={limit}&manufacturer_id={apple_manufacturer_id}'

while offset <= total:
    pages = snipe_api_call(f'{page}&offset={offset}', method='GET')
    offset += limit

    total = pages['total']
    serials = {}
    for asset in pages['rows']:
        serial = asset['serial'].lower()
        if (asset['purchase_date'] or
                serial.startswith('sccm-') or serial.startswith('ordr-') or serial.startswith('ans-')):
            continue

        shipDate = query_apple_warranty(asset['serial'], model_name=asset['model']['name'])

        if not shipDate:
            continue

        date_string = shipDate.strftime('%Y-%m-%d')

        payload = {'purchase_date': date_string, 'warranty_months': 36}
        snipe_api_call(f"hardware/{asset['id']}", method='PATCH', payload=payload)
