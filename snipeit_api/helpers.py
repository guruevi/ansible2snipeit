from __future__ import annotations

import logging
import re
import smtplib
from csv import reader
from datetime import date, timedelta, datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import path

from typing import Any
from json import dumps as json_stringify

from snipeit_api.api import SnipeITApi
from snipeit_api.defaults import DEFAULTS


def clean_edr(value: Any) -> str:
    if not value:
        return ''

    valid_options = [
        "Antivirus (Manual)",
        "Avast Antivirus",
        "Bitdefender EDR Agent",
        "Carbon Black",
        "Check Point Endpoint Security",
        "Cortex XDR",
        "CrowdStrike Falcon",
        "Cylance OPTICS",
        "Cylance PROTECT",
        "Defender ATP",
        "Digital Guardian Agent",
        "ESET Endpoint Antivirus",
        "F-Secure Protection Service",
        "FireEye Endpoint Agent",
        "FortiClient",
        "Intercept X",
        "Kaspersky Endpoint Security",
        "Malwarebytes Client",
        "McAfee Agent",
        "Microsoft Defender ATP",
        "N/A (Manual)",
        "Norton 360",
        "SentinelOne",
        "Symantec Endpoint Protection",
        "Tanium Client",
        "Tenable Nessus",
        "Trend Micro Security Agent",
        "XProtect"
    ]

    if value in valid_options:
        return value

    print("Invalid EDR value: " + value)
    return ''


def clean_tag(value: Any) -> str:
    if not value:
        return ''
    # + does weird things, % is a wildcard, so it becomes hard to search for something with it
    # " and ' are used to delimit strings and can cause havoc
    value = str(value).replace('+', '').replace('%', '').replace('"', '').replace("'", '').strip()
    value_lower = value.lower()

    invalid = ["not available",
               "default string",
               "not specified",
               "null",
               "none",
               "empty",
               "unknown",
               # What vendor does this (SuperMicro)?
               "main board",
               "0000000000",
               "______________",  # NEC
               "123-1234-123",
               "..................",
               # LG Gram does this
               "type3serialnumber",
               # Siemens Simatic PLCs
               "simatic",
               # Mostly SuperMicro
               "system product name",
               "system manufacturer",
               "no asset tag",
               "chassis serial number",
               "undefined serial number",
               "chassis asset tag",
               # Azure VMs all have the same asset tag/serial numbers
               # https://learn.microsoft.com/en-us/azure/automation/troubleshoot/update-agent-issues-linux
               "7783-7084-3265-9085-8269-3286-77",
               # More vendor shenanigans
               "varian",
               "tangent197",
               "isd_pcs",
               # WTF Dell
               "unidentified system",
               "cbx3___",
               "n/a"]

    # Len < 3 also eliminates, 0, na and a few other strings that are not useful
    if not value_lower or len(value_lower) < 3 or value_lower in invalid:
        return ''

    # Spaces are intentional to make sure we don't match on partial words
    if ('to be filled' in value_lower or
            'system ' in value_lower or
            '123456789' in value_lower or
            # apparently all Bosch camera systems have the same serial/asset tag...
            value_lower.startswith('dip-')):
        return ''

    if 'series' in value_lower:
        value = value.split('series')[0]

    # logging.debug(f"Clean tag: {value}")
    return str(value).strip()


def clean_manufacturer(manufacturer: str):
    if not manufacturer:
        return ''

    manufacturer_lower = str(manufacturer).lower().strip()
    if manufacturer_lower.startswith('apple'):
        return 'Apple'
    elif manufacturer_lower.startswith('dell') or manufacturer_lower.endswith('ell inc.'):
        return 'Dell Inc.'
    elif manufacturer_lower.startswith('aaeon'):
        return 'AAEON Technology Inc.'
    elif manufacturer_lower.startswith('apc'):
        return 'APC'
    elif manufacturer_lower.startswith('alaris') or manufacturer_lower == 'becton dickinson':
        return 'BD'
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
    elif manufacturer_lower.startswith('b&r'):
        return 'BR Industrial Automation'
    elif manufacturer_lower.startswith('belkin'):
        return 'Belkin International Inc.'
    elif manufacturer_lower.startswith('bizlink'):
        return 'BizLink (Kunshan) Co.,Ltd'
    elif manufacturer_lower.startswith('brady'):
        return 'Brady Corporation'
    elif manufacturer_lower.startswith('broadcom'):
        return 'Broadcom Inc.'
    elif manufacturer_lower.startswith('buffalo'):
        return 'Buffalo Inc.'
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
    # Do not match on GETAC
    elif manufacturer_lower == 'ge' or 'general elec' in manufacturer_lower:
        return 'GE'
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
    elif manufacturer_lower.startswith('samsung'):
        return 'Samsung'
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

    return clean_tag(manufacturer)


def clean_mac(mac_address: str, remove_bad_vendors: bool = True) -> str:
    if not mac_address:
        return ''
    # Remove everything that is not a hex character, make it uppercase
    mac_address = ''.join(c for c in mac_address.upper() if c in '0123456789ABCDEF')
    # Invalid MAC
    if not mac_address or len(mac_address) != 12:
        return ''

    # Random MAC addresses x2, x6, xA, xE are reserved for local use
    # This catches Microsoft Loopback, VirtualBox, GlobalProtect and Apple Private addresses
    if mac_address[1] in ['2', '6', 'A', 'E'] and not (
            mac_address[:5] in DEFAULTS['valid_private_mac'] or
            mac_address[:6] in DEFAULTS['valid_private_mac'] or
            mac_address[:7] in DEFAULTS['valid_private_mac'] or
            mac_address[:8] in DEFAULTS['valid_private_mac']
    ):
        return ''

    if mac_address == '000000000000' or mac_address == 'FFFFFFFFFFFF':
        return ''

    # Bad MAC addresses, typically due to being USB dongles
    # 000000 -> Xerox (not invalid)
    # 0A:00:27:00:00:00 -> VirtualBox
    bad_prefix = [
        # HyperV network adapters, haven't noticed duplicates yet
        # '00155D',
        # VMWare network adapters, no duplicates on server products yet
        # '005056',
        # This one seems to be VMware desktop products which are consecutively assigned
        '005056C0',
        # Belkin (USB network adapters)
        '00173F', '001CDF', '002275', '08863B', '149182', '24F5A2', '302303', '58EF68',
        '6038E0', '80691A', '94103E', '944452', 'B4750E', 'C05627', 'C4411E', 'D8EC5E',
        'E89F80', 'EC1A59',
        '001150', '0030BD',
        # CE Link (USB network adapters)
        '6C6E07', '70B3D554', 'A0CEC8',
        # Cable Matters (USB network adapters)
        'F44DAD', '5C857E30', '70886B80',
        # Cisco AnyConnect
        '00059A3C7A00', '00059A3C7800',
        # Apple USB dongles
        '5CF7E68B',
        'AC7F3EE6DDE5',
        # Microsoft USB dongles?
        'F01DBCF2',
        # ASIX USB dongles
        'F8E43B',
        # BizLink (Kunshan) USB dongles
        '9CEBE8',
        # Speed Dragon Multimedia USB dongle
        '00133B',
        # AuKey (Dongguan Kingtron Electronics Tech Co., Ltd) USB dongles
        '98FC84E',
        '34298F7',
        #  Wistron Infocomm (Zhongshan) Corporation dongle
        '98EECBB21088',
        # OmniKey RFID dongle virtual MAC
        # These are serially generated (00, 01, ...) and not unique
        '00189E',
        # Realtek USB dongles
        '00E04C'
        # Cisco-Linksys dongles
        'C8D719C3426D',
        # Dell USB dongle
        '509A4C1B0BC4',
        '605B3021',
        'C025A5ED7191',
        '3C2C30F82A34',
        # Luxshare Precision Industry Company Limited
        '3C18A0',
        # Tp-Link Technologies Co.,Ltd.
        '984827',
        '34E894',
        # Shenzen Cudy Technology Co., Ltd.
        'B44BD62',
        # Shenzhen Century Xinyang Technology Co., Ltd
        '90DE80',
        # Good Way Ind. Co., Ltd.
        "0050B6",
        # TRENDnet, Inc.
        "782D7E",
        # Wistron InfoComm(Kunshan)Co.,Ltd. - Lenovo Docking Stations
        "54EE75",
        # Hon Hai Precision Ind. Co.,Ltd.
        "FC017C"
    ]
    # :11 is /28
    if remove_bad_vendors and (mac_address in bad_prefix or
                               mac_address[:8] in bad_prefix or
                               mac_address[:7] in bad_prefix or
                               mac_address[:6] in bad_prefix or
                               mac_address[:5] in bad_prefix):
        return ''

    # Add colons
    mac_address = ':'.join(mac_address[i:i + 2] for i in range(0, 12, 2))

    return mac_address


def clean_os(operating_system: str) -> str:
    if operating_system == 'Red Hat':
        return "RedHat"
    if "Monterey" in operating_system:
        return "macOS"
    if operating_system.startswith("Mac OS 10"):
        return "Mac OS X"
    if operating_system.startswith("Microsoft "):
        return operating_system[10:]
    return operating_system


def clean_ip(ip: Any) -> str | None:
    # Validate this is an IPv4 address
    if not ip:
        return None
    ip = str(ip).strip()
    try:
        ip = ip.split(".")
        if len(ip) != 4:
            return None
        for octet in ip:
            octet = int(octet)
            if octet < 1 or octet > 254:
                return None
    except ValueError:
        return None

    # Check if this is a bogus IP address
    if int(ip[0]) in [127, 255]:
        return None
    if int(ip[0]) == 169 and int(ip[1]) == 254:
        return None
    if int(ip[0]) in range(224, 239):
        return None

    return ".".join(ip)


def filter_list(value: list[Any]) -> list[Any]:
    value = list(set([x for x in value if x]))
    value.sort()
    return value


def filter_list_str(value: list[Any]) -> list[str]:
    value = list(set([str(x) for x in value if x]))
    value.sort()
    return value


def filter_list_first(value: list[Any]) -> Any:
    value = filter_list(value)
    return value[0] if value else None


def clean_user(user: str) -> str:
    invalid = ["not available",
               "default string",
               "not specified",
               "null",
               "none",
               "empty",
               "unknown",
               "root",
               "system"]
    # Make sure user is str
    user = str(user).strip().lower()
    if not user or user in invalid:
        return ''
    if "scanner" in user or "admin" in user:
        return ''
    # If @ in user or \\ in user, strip domain
    if "@" in user:
        user = user.split('@')[0]
    if "\\" in user:
        user = user.split("\\")[-1]

    return user


def get_os_type(operating_system: str) -> str:
    os = operating_system.lower()
    if "windows" in os:
        return "Windows"
    if ("linux" in os or
            "ubuntu" in os or
            "debian" in os or
            "redhat" in os or
            "red hat" in os or
            "centos" in os or
            "fedora" in os or
            "suse" in os or
            "alma" in os or
            "rhel" in os or
            "centos" in os or
            "evolution" in os):
        return "Linux"
    if ("mac" in os or
            "android" in os or
            os == "ios" or
            "tvos" in os or
            "watchos" in os or
            "bsd" in os or
            "cisco" in os or
            "chrome" in os or
            "vxworks" in os or
            "other" in os):
        return "Other"
    if ("apc" in os or
            "axis" in os or
            "cobos" in os or
            "enea" in os or
            "futuresmart" in os or
            "pump" in os or
            "roku" in os or
            "proprietary" in os):
        return "Proprietary"
    return ""


def validate_os(operating_system: str, valid_os: list = None) -> str:
    operating_system = clean_os(operating_system)
    if not valid_os:
        valid_os = DEFAULTS['valid_os']

    if operating_system in valid_os:
        return operating_system

    return ""


def validate_category(category: str, valid_categories: list = None) -> str:
    if not category:
        return ""
    if not valid_categories:
        valid_categories = DEFAULTS['valid_categories']
    if category in valid_categories:
        return category
    return ""


def convert_to_bool(value: str) -> bool:
    if value.lower() in ['yes', 'true', '1', 'y']:
        return True
    return False


def print_progress(current: int, total: int):
    if not total:
        return
    print(json_stringify({"progress": round(current / total, 2)}))


def query_apple_warranty(serial: str, model_name: str='') -> date|None:
    # http://www.macrumors.com/2010/04/16/apple-tweaks-serial-number-format-with-new-macbook-pro/
    year_regexp = re.compile(r'\d{4}')
    year_re = year_regexp.search(model_name)

    if not year_re:
        model_years = {
            "iPad 7th Generation (Wi-Fi)": 2019,
            "iPad Pro (12.9-inch) (6th generation)": 2022,
            "iPad Pro (12.9-inch Cellular) (4th Generation)": 2020,
            "iPad 9th generation (Wi-Fi)": 2021,
            "iPad Pro 13-inch (M4)": 2024,
            "iPad Pro 11-inch (M4)": 2024,
            "iPad Air 13-inch (M2)": 2024,
            "iPad Air 11-inch (M2)": 2024,
            "iPad 10th Generation (Wi-Fi/Cellular)": 2022,
            "Mac Studio": 2022,
            "Macbook Pro 14 inch M4": 2024,
            "Macbook Pro 16 inch M4 Max": 2024,
            "iMac 24 inch Four Thunderbolt Ports": 2023,
        }
        year = model_years.get(model_name, None)
    else:
        year = int(year_re.group())

    # If for whatever reason we get 0 or None, return None
    if not year:
        return None

    # Apple changed format in 2010
    if len(serial) == 11 and year < 2013:
        # Old format
        year = serial[2].lower()
        est_year = 2000 + '   3456789012'.index(year)
        week = int(serial[3:5]) - 1
        year_time = date(year=est_year, month=1, day=1)
        if week:
            week_dif = timedelta(weeks=int(week))
            year_time += week_dif

        return year_time
    # Changed format until 2020 after which they are truly randomized
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
        year_time = date(year=est_year, month=1, day=1)
        if est_week:
            week_dif = timedelta(weeks=int(est_week))
            year_time += week_dif
        return year_time

    return date(year=year, month=1, day=1)


def validate_hostname(hostname) -> str:
    if not hostname:
        return ''
    hostname = str(hostname).strip().upper()
    # Regular expression pattern for a valid short hostname or FQDN
    short_hostname_pattern = r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$"
    fqdn_pattern = r"^(?=[a-zA-Z0-9-]{1,63}\.)([a-zA-Z0-9-]{1,63}\.?)+([a-zA-Z]{2,63})$"
    short_hostname_regex = re.compile(short_hostname_pattern)
    fqdn_regex = re.compile(fqdn_pattern)

    # Check if the name matches the patterns
    if short_hostname_regex.match(hostname):
        return hostname
    elif fqdn_regex.match(hostname):
        return hostname.split('.')[0]
    else:
        return ''


def send_email(recipient_email, subject, body, sender_email,
               server: str = 'localhost', server_port: int = 25, attachment_path: str = ''):
    # Create a multipart message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Add body to email
    msg.attach(MIMEText(body, 'plain'))

    # Attach log file
    if attachment_path:
        with open(attachment_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {attachment_path.split(path.sep)[-1]}')

    msg.attach(part)

    # Connect to the SMTP server
    server = smtplib.SMTP(server, server_port)
    # Send email
    text = msg.as_string()
    server.sendmail(sender_email, recipient_email, text)

    # Close the connection
    server.quit()


DEPT_OU = {}
LAB_OU = {}
def get_depts():
    global DEPT_OU
    global LAB_OU
    if DEPT_OU:
        return DEPT_OU

    # Read in the CSV file into a global variable
    with open('ou_dept.csv', 'r') as f:
        for row in reader(f):
            DEPT_OU[row[0]] = row[1]
            LAB_OU[row[0]] = row[2]

    return DEPT_OU

def get_labs():
    global LAB_OU
    if not LAB_OU:
        get_depts()
    return LAB_OU

def get_dept_from_ou(ou: str):
    depts = get_depts()
    # Start by searching for the entire string, then remove the last part and try again
    while ou:
        if ou in depts:
            return depts[ou]
        ou = '/'.join(ou.split('/')[:-1])

    return ''

def get_lab_from_ou(ou: str):
    labs = get_labs()

    while ou:
        if ou in labs:
            return labs[ou]
        ou = '/'.join(ou.split('/')[:-1])

    return ''

def parse_isoformat(date_string):
    if date_string.endswith('Z'):
        date_string = date_string[:-1] + '+00:00'
    return datetime.fromisoformat(date_string)
