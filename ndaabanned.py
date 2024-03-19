#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Search SnipeIT for NDAA banned devices
# This will get a list of systems matching a MAC address prefix and put them into Snipe-IT as "need-to-audit" assets.
import logging
from configparser import RawConfigParser

from snipeit_api.api import SnipeITApi

logging.basicConfig(level=logging.INFO)
CONFIG = RawConfigParser()
logging.debug("Checking for a settings.conf ...")
CONFIG.read("settings.conf")
snipeit_apiurl = CONFIG.get('snipe-it', 'url')
snipeit_apikey = CONFIG.get('snipe-it', 'apikey')

snipe_api = SnipeITApi(url=snipeit_apiurl, api_key=snipeit_apikey)


# ZTE MAC prefix
zte_mac_prefix = ['00:15:EB',
                  '00:19:C6',
                  '00:1E:73',
                  '00:22:93',
                  '00:25:12',
                  '00:26:ED',
                  '00:4A:77',
                  '00:E7:E3',
                  '04:1D:C7',
                  '04:20:84',
                  '04:95:73',
                  '08:18:1A',
                  '08:3F:BC',
                  '08:60:83',
                  '08:9A:C7',
                  '08:AA:89',
                  '08:E6:3B',
                  '08:F6:06',
                  '0C:01:4B',
                  '0C:12:62',
                  '0C:37:47',
                  '0C:72:D9',
                  '10:10:81',
                  '10:12:D0',
                  '10:3C:59',
                  '10:D0:AB',
                  '14:00:7D',
                  '14:09:B4',
                  '14:3E:BF',
                  '14:60:80',
                  '14:6B:9A',
                  '14:CA:56',
                  '18:13:2D',
                  '18:44:E6',
                  '18:5E:0B',
                  '18:68:6A',
                  '18:79:FD',
                  '1C:27:04',
                  '1C:67:4A',
                  '20:08:89',
                  '20:10:8A',
                  '20:3A:EB',
                  '20:89:86',
                  '20:E8:82',
                  '24:58:6E',
                  '24:7E:51',
                  '24:A6:5E',
                  '24:C4:4A',
                  '24:D3:F2',
                  '28:01:1C',
                  '28:77:77',
                  '28:7B:09',
                  '28:8C:B8',
                  '28:C8:7C',
                  '28:DE:A8',
                  '28:FF:3E',
                  '2C:26:C5',
                  '2C:70:4F',
                  '2C:95:7F',
                  '2C:F1:BB',
                  '30:0C:23',
                  '30:1F:48',
                  '30:40:74',
                  '30:42:40',
                  '30:99:35',
                  '30:B9:30',
                  '30:CC:21',
                  '30:D3:86',
                  '30:DC:E7',
                  '30:F3:1D',
                  '34:24:3E',
                  '34:36:54',
                  '34:37:59',
                  '34:4B:50',
                  '34:4D:EA',
                  '34:69:87',
                  '34:78:39',
                  '34:DA:B7',
                  '34:DE:34',
                  '34:E0:CF',
                  '38:46:08',
                  '38:54:9B',
                  '38:6E:88',
                  '38:90:AF',
                  '38:9E:80',
                  '38:D8:2F',
                  '38:E1:AA',
                  '38:E2:DD',
                  '38:F6:CF',
                  '3C:6F:9B',
                  '3C:A7:AE',
                  '3C:BC:D0',
                  '3C:DA:2A',
                  '3C:F6:52',
                  '3C:F9:F0',
                  '40:0E:F3',
                  '44:13:D0',
                  '44:32:62',
                  '44:41:F0',
                  '44:59:43',
                  '44:A3:C7',
                  '44:F4:36',
                  '44:FB:5A',
                  '44:FF:BA',
                  '48:28:2F',
                  '48:59:A4',
                  '48:5F:DF',
                  '48:A7:4E',
                  '4C:09:B4',
                  '4C:16:F1',
                  '4C:49:4F',
                  '4C:4C:D8',
                  '4C:AB:FC',
                  '4C:AC:0A',
                  '4C:CB:F5',
                  '50:42:89',
                  '50:5D:7A',
                  '50:78:B3',
                  '50:AF:4D',
                  '50:E2:4E',
                  '54:09:55',
                  '54:1F:8D',
                  '54:22:F8',
                  '54:46:17',
                  '54:84:DC',
                  '54:BE:53',
                  '54:CE:82',
                  '54:DE:D3',
                  '58:5F:F6',
                  '58:D3:12',
                  '58:FF:A1',
                  '5C:10:1E',
                  '5C:3A:3D',
                  '5C:4D:BF',
                  '5C:A4:F4',
                  '5C:BB:EE',
                  '60:14:66',
                  '60:18:88',
                  '60:73:BC',
                  '64:13:6C',
                  '64:6E:60',
                  '64:85:05',
                  '64:DB:38',
                  '68:1A:B2',
                  '68:27:5F',
                  '68:77:DA',
                  '68:8A:F0',
                  '68:94:4A',
                  '68:9E:29',
                  '68:9F:F0',
                  '6C:8B:2F',
                  '6C:A7:5F',
                  '6C:B8:81',
                  '6C:D2:BA',
                  '70:11:0E',
                  '70:2E:22',
                  '70:9F:2D',
                  '74:26:FF',
                  '74:33:E9',
                  '74:4A:A4',
                  '74:6F:88',
                  '74:97:81',
                  '74:A7:8E',
                  '74:B5:7E',
                  '78:1D:4A',
                  '78:31:2B',
                  '78:90:A2',
                  '78:96:82',
                  '78:C1:A7',
                  '78:E8:B6',
                  '7C:39:53',
                  '7C:B3:0A',
                  '80:2D:1A',
                  '80:7C:0A',
                  '80:B0:7B',
                  '84:13:9F',
                  '84:1C:70',
                  '84:3C:99',
                  '84:74:2A',
                  '84:74:60',
                  '84:93:B2',
                  '84:F5:EB',
                  '88:5D:FB',
                  '88:7B:2C',
                  '88:C1:74',
                  '88:D2:74',
                  '8C:14:B4',
                  '8C:68:C8',
                  '8C:79:67',
                  '8C:8E:0D',
                  '8C:DC:02',
                  '8C:E0:81',
                  '8C:E1:17',
                  '8C:EE:FD',
                  '90:1D:27',
                  '90:79:CF',
                  '90:7E:43',
                  '90:86:9B',
                  '90:C7:10',
                  '90:C7:D8',
                  '90:D4:32',
                  '90:D8:F3',
                  '90:FD:73',
                  '94:28:6F',
                  '94:98:69',
                  '94:A7:B7',
                  '94:BF:80',
                  '94:CB:CD',
                  '94:E3:EE',
                  '98:00:6A',
                  '98:13:33',
                  '98:17:F1',
                  '98:66:10',
                  '98:6C:F5',
                  '98:9A:B9',
                  '98:EE:8C',
                  '98:F4:28',
                  '98:F5:37',
                  '9C:2F:4E',
                  '9C:63:5B',
                  '9C:63:ED',
                  '9C:6F:52',
                  '9C:A9:E4',
                  '9C:B4:00',
                  '9C:D2:4B',
                  '9C:E9:1C',
                  'A0:09:2E',
                  'A0:10:77',
                  'A0:91:C8',
                  'A0:CF:F5',
                  'A0:EC:80',
                  'A4:40:27',
                  'A4:7E:39',
                  'A4:F3:3B',
                  'A8:02:DB',
                  'A8:74:84',
                  'A8:A6:68',
                  'AC:00:D0',
                  'AC:64:62',
                  'AC:AD:4B',
                  'B0:0A:D5',
                  'B0:75:D5',
                  'B0:8B:92',
                  'B0:AC:D2',
                  'B0:B1:94',
                  'B0:C1:9E',
                  'B4:04:21',
                  'B4:1C:30',
                  'B4:5F:84',
                  'B4:98:42',
                  'B4:B3:62',
                  'B4:DE:DF',
                  'B8:05:AB',
                  'B8:D4:BC',
                  'B8:DD:71',
                  'B8:F0:B9',
                  'BC:16:95',
                  'BC:BD:84',
                  'BC:F4:5F',
                  'BC:F8:8B',
                  'C0:49:43',
                  'C0:51:5C',
                  'C0:92:96',
                  'C0:94:AD',
                  'C0:9F:E1',
                  'C0:B1:01',
                  'C0:FD:84',
                  'C4:21:B9',
                  'C4:27:28',
                  'C4:74:1E',
                  'C4:A3:66',
                  'C4:EB:FF',
                  'C8:4C:78',
                  'C8:5A:9F',
                  'C8:64:C7',
                  'C8:7B:5B',
                  'C8:98:28',
                  'C8:EA:F8',
                  'CC:1A:FA',
                  'CC:29:BD',
                  'CC:7B:35',
                  'CC:A0:8F',
                  'D0:15:4A',
                  'D0:58:A8',
                  'D0:59:19',
                  'D0:5B:A8',
                  'D0:60:8C',
                  'D0:71:C4',
                  'D0:BB:61',
                  'D0:C7:30',
                  'D0:DD:7C',
                  'D0:F9:28',
                  'D0:F9:9B',
                  'D4:37:D7',
                  'D4:72:26',
                  'D4:76:EA',
                  'D4:9E:05',
                  'D4:B7:09',
                  'D4:C1:C8',
                  'D4:F7:56',
                  'D8:09:7F',
                  'D8:0A:E6',
                  'D8:31:2C',
                  'D8:4A:2B',
                  'D8:55:A3',
                  'D8:74:95',
                  'D8:8C:73',
                  'D8:A0:E8',
                  'D8:A8:C8',
                  'D8:E8:44',
                  'DC:02:8E',
                  'DC:36:42',
                  'DC:51:93',
                  'DC:68:80',
                  'DC:71:37',
                  'DC:DF:D6',
                  'DC:E5:D8',
                  'DC:F8:B9',
                  'E0:19:54',
                  'E0:38:3F',
                  'E0:41:02',
                  'E0:7C:13',
                  'E0:A1:CE',
                  'E0:B6:68',
                  'E0:C3:F3',
                  'E4:47:B3',
                  'E4:60:4D',
                  'E4:66:AB',
                  'E4:77:23',
                  'E4:7E:9A',
                  'E4:BD:4B',
                  'E4:CA:12',
                  'E8:43:68',
                  'E8:6E:44',
                  'E8:81:75',
                  'E8:A1:F8',
                  'E8:AC:AD',
                  'E8:B5:41',
                  'EC:1D:7F',
                  'EC:23:7B',
                  'EC:6C:B5',
                  'EC:82:63',
                  'EC:8A:4C',
                  'EC:C3:B0',
                  'EC:F0:FE',
                  'F0:1B:24',
                  'F0:84:C9',
                  'F0:AB:1F',
                  'F4:12:DA',
                  'F4:1F:88',
                  'F4:2D:06',
                  'F4:2E:48',
                  'F4:3A:7B',
                  'F4:6D:E2',
                  'F4:B5:AA',
                  'F4:B8:A7',
                  'F4:E4:AD',
                  'F4:E8:4F',
                  'F4:F6:47',
                  'F8:0D:F0',
                  'F8:56:C3',
                  'F8:64:B8',
                  'F8:79:28',
                  'F8:A3:4F',
                  'F8:DF:A8',
                  'FC:2D:5E',
                  'FC:40:09',
                  'FC:44:9F',
                  'FC:8A:3D',
                  'FC:8A:F7',
                  'FC:94:CE',
                  'FC:C8:97',
                  'FC:FA:21',
                  ]

# Huawei MAC prefix
huawei_mac_prefix = ['00:18:82',  # Huawei Technologies Co.,Ltd
                     '00:1E:10',  # Huawei Technologies Co.,Ltd
                     '00:22:A1',  # Huawei Symantec Technologies Co.,Ltd.
                     '00:25:68',  # Huawei Technologies Co.,Ltd
                     '00:25:9E',  # Huawei Technologies Co.,Ltd
                     '00:2E:C7',  # Huawei Technologies Co.,Ltd
                     '00:34:FE',  # Huawei Technologies Co.,Ltd
                     '00:3D:E1',  # Huawei Device Co., Ltd.
                     '00:46:4B',  # Huawei Technologies Co.,Ltd
                     '00:4F:1A',  # Huawei Technologies Co.,Ltd
                     '00:56:6D',  # Huawei Device Co., Ltd.
                     '00:5A:13',  # Huawei Technologies Co.,Ltd
                     '00:61:51',  # Huawei Technologies Co.,Ltd
                     '00:66:19',  # Huawei Device Co., Ltd.
                     '00:66:4B',  # Huawei Technologies Co.,Ltd
                     '00:68:2B',  # Huawei Device Co., Ltd.
                     '00:6B:6F',  # Huawei Technologies Co.,Ltd
                     '00:8A:55',  # Huawei Device Co., Ltd.
                     '00:94:EC',  # Huawei Device Co., Ltd.
                     '00:99:1D',  # Huawei Technologies Co.,Ltd
                     '00:9A:CD',  # Huawei Technologies Co.,Ltd
                     '00:A4:5F',  # Huawei Device Co., Ltd.
                     '00:AD:D5',  # Huawei Device Co., Ltd.
                     '00:BB:1C',  # Huawei Device Co., Ltd.
                     '00:BE:3B',  # Huawei Technologies Co.,Ltd
                     '00:D8:A2',  # Huawei Device Co., Ltd.
                     '00:E0:FC',  # Huawei Technologies Co.,Ltd
                     '00:E4:06',  # Huawei Technologies Co.,Ltd
                     '00:F7:AD',  # Huawei Technologies Co.,Ltd
                     '00:F8:1C',  # Huawei Technologies Co.,Ltd
                     '00:F9:52',  # Huawei Technologies Co.,Ltd
                     '04:02:1F',  # Huawei Technologies Co.,Ltd
                     '04:14:71',  # Huawei Technologies Co.,Ltd
                     '04:18:92',  # Huawei Technologies Co.,Ltd
                     '04:25:C5',  # Huawei Technologies Co.,Ltd
                     '04:27:58',  # Huawei Technologies Co.,Ltd
                     '04:33:1F',  # Huawei Device Co., Ltd.
                     '04:33:89',  # Huawei Technologies Co.,Ltd
                     '04:49:5D',  # Huawei Device Co., Ltd.
                     '04:4A:6C',  # Huawei Technologies Co.,Ltd
                     '04:4F:4C',  # Huawei Technologies Co.,Ltd
                     '04:63:D0',  # Huawei Device Co., Ltd.
                     '04:75:03',  # Huawei Technologies Co.,Ltd
                     '04:79:70',  # Huawei Technologies Co.,Ltd
                     '04:7A:AE',  # Huawei Device Co., Ltd.
                     '04:88:5F',  # Huawei Technologies Co.,Ltd
                     '04:8C:16',  # Huawei Technologies Co.,Ltd
                     '04:8C:9A',  # Huawei Device Co., Ltd.
                     '04:9F:CA',  # Huawei Technologies Co.,Ltd
                     '04:A8:1C',  # Huawei Technologies Co.,Ltd
                     '04:B0:E7',  # Huawei Technologies Co.,Ltd
                     '04:BA:1C',  # Huawei Device Co., Ltd.
                     '04:BD:70',  # Huawei Technologies Co.,Ltd
                     '04:C0:6F',  # Huawei Technologies Co.,Ltd
                     '04:C1:D8',  # Huawei Device Co., Ltd.
                     '04:CA:ED',  # Huawei Technologies Co.,Ltd
                     '04:CC:BC',  # Huawei Technologies Co.,Ltd
                     '04:D3:B5',  # Huawei Device Co., Ltd.
                     '04:E7:95',  # Huawei Technologies Co.,Ltd
                     '04:F0:3E',  # Huawei Device Co., Ltd.
                     '04:F1:69',  # Huawei Device Co., Ltd.
                     '04:F3:52',  # Huawei Technologies Co.,Ltd
                     '04:F9:38',  # Huawei Technologies Co.,Ltd
                     '04:FE:8D',  # Huawei Technologies Co.,Ltd
                     '04:FF:08',  # Huawei Device Co., Ltd.
                     '08:02:05',  # Huawei Technologies Co.,Ltd
                     '08:19:A6',  # Huawei Technologies Co.,Ltd
                     '08:1A:FD',  # Huawei Device Co., Ltd.
                     '08:23:C6',  # Huawei Technologies Co.,Ltd
                     '08:27:6B',  # Huawei Device Co., Ltd.
                     '08:2E:36',  # Huawei Device Co., Ltd.
                     '08:2F:E9',  # Huawei Technologies Co.,Ltd
                     '08:31:8B',  # Huawei Technologies Co.,Ltd
                     '08:31:A4',  # Huawei Device Co., Ltd.
                     '08:4F:0A',  # Huawei Technologies Co.,Ltd
                     '08:51:04',  # Huawei Device Co., Ltd.
                     '08:5C:1B',  # Huawei Technologies Co.,Ltd
                     '08:63:61',  # Huawei Technologies Co.,Ltd
                     '08:6E:9C',  # Huawei Device Co., Ltd.
                     '08:70:73',  # Huawei Technologies Co.,Ltd
                     '08:79:8C',  # Huawei Technologies Co.,Ltd
                     '08:7A:4C',  # Huawei Technologies Co.,Ltd
                     '08:93:56',  # Huawei Technologies Co.,Ltd
                     '08:9E:84',  # Huawei Technologies Co.,Ltd
                     '08:A8:42',  # Huawei Device Co., Ltd.
                     '08:C0:21',  # Huawei Technologies Co.,Ltd
                     '08:C0:6C',  # Huawei Device Co., Ltd.
                     '08:E7:E5',  # Huawei Device Co., Ltd.
                     '08:E8:4F',  # Huawei Technologies Co.,Ltd
                     '08:EB:F6',  # Huawei Technologies Co.,Ltd
                     '08:F4:58',  # Huawei Device Co., Ltd.
                     '08:FA:28',  # Huawei Technologies Co.,Ltd
                     '0C:17:73',  # Huawei Device Co., Ltd.
                     '0C:18:4E',  # Huawei Technologies Co.,Ltd
                     '0C:2C:54',  # Huawei Technologies Co.,Ltd
                     '0C:2E:57',  # Huawei Technologies Co.,Ltd
                     '0C:31:DC',  # Huawei Technologies Co.,Ltd
                     '0C:37:DC',  # Huawei Technologies Co.,Ltd
                     '0C:41:E9',  # Huawei Technologies Co.,Ltd
                     '0C:45:BA',  # Huawei Technologies Co.,Ltd
                     '0C:4F:9B',  # Huawei Technologies Co.,Ltd
                     '0C:67:43',  # Huawei Technologies Co.,Ltd
                     '0C:70:4A',  # Huawei Technologies Co.,Ltd
                     '0C:83:9A',  # Huawei Device Co., Ltd.
                     '0C:84:08',  # Huawei Technologies Co.,Ltd
                     '0C:8F:FF',  # Huawei Technologies Co.,Ltd
                     '0C:96:BF',  # Huawei Technologies Co.,Ltd
                     '0C:B5:27',  # Huawei Technologies Co.,Ltd
                     '0C:BE:F1',  # Huawei Device Co., Ltd.
                     '0C:C6:CC',  # Huawei Technologies Co.,Ltd
                     '0C:D6:BD',  # Huawei Technologies Co.,Ltd
                     '0C:E4:A0',  # Huawei Device Co., Ltd.
                     '0C:FC:18',  # Huawei Technologies Co.,Ltd
                     '10:01:77',  # Huawei Technologies Co.,Ltd
                     '10:1B:54',  # Huawei Technologies Co.,Ltd
                     '10:24:07',  # Huawei Technologies Co.,Ltd
                     '10:32:1D',  # Huawei Technologies Co.,Ltd
                     '10:32:7E',  # Huawei Device Co., Ltd.
                     '10:44:00',  # Huawei Technologies Co.,Ltd
                     '10:47:80',  # Huawei Technologies Co.,Ltd
                     '10:51:72',  # Huawei Technologies Co.,Ltd
                     '10:5D:DC',  # Huawei Device Co., Ltd.
                     '10:71:00',  # Huawei Device Co., Ltd.
                     '10:8F:FE',  # Huawei Technologies Co.,Ltd
                     '10:9D:7A',  # Huawei Device Co., Ltd.
                     '10:A4:DA',  # Huawei Technologies Co.,Ltd
                     '10:B1:F8',  # Huawei Technologies Co.,Ltd
                     '10:C1:72',  # Huawei Technologies Co.,Ltd
                     '10:C3:AB',  # Huawei Technologies Co.,Ltd
                     '10:C6:1F',  # Huawei Technologies Co.,Ltd
                     '10:DA:49',  # Huawei Device Co., Ltd.
                     '10:E9:53',  # Huawei Device Co., Ltd.
                     '10:FC:33',  # Huawei Device Co., Ltd.
                     '14:09:DC',  # Huawei Technologies Co.,Ltd
                     '14:13:FB',  # Huawei Technologies Co.,Ltd
                     '14:23:0A',  # Huawei Technologies Co.,Ltd
                     '14:30:04',  # Huawei Technologies Co.,Ltd
                     '14:3C:C3',  # Huawei Technologies Co.,Ltd
                     '14:46:58',  # Huawei Technologies Co.,Ltd
                     '14:49:20',  # Huawei Technologies Co.,Ltd
                     '14:51:20',  # Huawei Device Co., Ltd.
                     '14:55:94',  # Huawei Device Co., Ltd.
                     '14:56:3A',  # Huawei Device Co., Ltd.
                     '14:57:9F',  # Huawei Technologies Co.,Ltd
                     '14:5F:94',  # Huawei Technologies Co.,Ltd
                     '14:65:6A',  # Huawei Technologies Co.,Ltd
                     '14:77:40',  # Huawei Device Co., Ltd.
                     '14:89:CB',  # Huawei Technologies Co.,Ltd
                     '14:8C:4A',  # Huawei Technologies Co.,Ltd
                     '14:9D:09',  # Huawei Technologies Co.,Ltd
                     '14:A0:F8',  # Huawei Technologies Co.,Ltd
                     '14:A3:2F',  # Huawei Device Co., Ltd.
                     '14:A3:B4',  # Huawei Device Co., Ltd.
                     '14:A5:1A',  # Huawei Technologies Co.,Ltd
                     '14:AB:02',  # Huawei Technologies Co.,Ltd
                     '14:B9:68',  # Huawei Technologies Co.,Ltd
                     '14:D1:1F',  # Huawei Technologies Co.,Ltd
                     '14:D1:69',  # Huawei Technologies Co.,Ltd
                     '14:DA:B9',  # Huawei Device Co., Ltd.
                     '14:DE:39',  # Huawei Device Co., Ltd.
                     '14:EB:08',  # Huawei Technologies Co.,Ltd
                     '14:FB:70',  # Huawei Device Co., Ltd.
                     '18:02:2D',  # Huawei Technologies Co.,Ltd
                     '18:2A:57',  # Huawei Technologies Co.,Ltd
                     '18:3C:B7',  # Huawei Device Co., Ltd.
                     '18:3D:5E',  # Huawei Technologies Co.,Ltd
                     '18:56:44',  # Huawei Technologies Co.,Ltd
                     '18:70:3B',  # Huawei Device Co., Ltd.
                     '18:9E:2C',  # Huawei Device Co., Ltd.
                     '18:AA:0F',  # Huawei Device Co., Ltd.
                     '18:BB:1C',  # Huawei Device Co., Ltd.
                     '18:BB:41',  # Huawei Device Co., Ltd.
                     '18:C0:07',  # Huawei Device Co., Ltd.
                     '18:C5:8A',  # Huawei Technologies Co.,Ltd
                     '18:CF:24',  # Huawei Technologies Co.,Ltd
                     '18:D2:76',  # Huawei Technologies Co.,Ltd
                     '18:D6:DD',  # Huawei Technologies Co.,Ltd
                     '18:D9:8F',  # Huawei Device Co., Ltd.
                     '18:DE:D7',  # Huawei Technologies Co.,Ltd
                     '18:E9:1D',  # Huawei Technologies Co.,Ltd
                     '1C:13:86',  # Huawei Device Co., Ltd.
                     '1C:15:1F',  # Huawei Technologies Co.,Ltd
                     '1C:1D:67',  # Huawei Technologies Co.,Ltd
                     '1C:1F:F1',  # Huawei Device Co., Ltd.
                     '1C:20:DB',  # Huawei Technologies Co.,Ltd
                     '1C:3C:D4',  # Huawei Technologies Co.,Ltd
                     '1C:3D:2F',  # Huawei Technologies Co.,Ltd
                     '1C:43:63',  # Huawei Technologies Co.,Ltd
                     '1C:47:2F',  # Huawei Device Co., Ltd.
                     '1C:59:9B',  # Huawei Technologies Co.,Ltd
                     '1C:67:58',  # Huawei Technologies Co.,Ltd
                     '1C:73:E2',  # Huawei Technologies Co.,Ltd
                     '1C:7F:2C',  # Huawei Technologies Co.,Ltd
                     '1C:8E:5C',  # Huawei Technologies Co.,Ltd
                     '1C:A6:81',  # Huawei Technologies Co.,Ltd
                     '1C:AE:CB',  # Huawei Technologies Co.,Ltd
                     '1C:B7:96',  # Huawei Technologies Co.,Ltd
                     '1C:E5:04',  # Huawei Technologies Co.,Ltd
                     '1C:E6:39',  # Huawei Technologies Co.,Ltd
                     '1C:E6:AD',  # Huawei Device Co., Ltd.
                     '1C:F4:2B',  # Huawei Device Co., Ltd.
                     '20:08:ED',  # Huawei Technologies Co.,Ltd
                     '20:0B:C7',  # Huawei Technologies Co.,Ltd
                     '20:28:3E',  # Huawei Technologies Co.,Ltd
                     '20:2B:C1',  # Huawei Technologies Co.,Ltd
                     '20:3D:B2',  # Huawei Technologies Co.,Ltd
                     '20:53:83',  # Huawei Technologies Co.,Ltd
                     '20:54:FA',  # Huawei Technologies Co.,Ltd
                     '20:5E:64',  # Huawei Device Co., Ltd.
                     '20:65:8E',  # Huawei Technologies Co.,Ltd
                     '20:6B:F4',  # Huawei Device Co., Ltd.
                     '20:87:EC',  # Huawei Technologies Co.,Ltd
                     '20:8C:86',  # Huawei Technologies Co.,Ltd
                     '20:A6:80',  # Huawei Technologies Co.,Ltd
                     '20:A7:66',  # Huawei Technologies Co.,Ltd
                     '20:AB:48',  # Huawei Technologies Co.,Ltd
                     '20:DA:22',  # Huawei Technologies Co.,Ltd
                     '20:DC:FD',  # Huawei Device Co., Ltd.
                     '20:DF:73',  # Huawei Technologies Co.,Ltd
                     '20:F1:7C',  # Huawei Technologies Co.,Ltd
                     '20:F3:A3',  # Huawei Technologies Co.,Ltd
                     '24:00:BA',  # Huawei Technologies Co.,Ltd
                     '24:01:6F',  # Huawei Device Co., Ltd.
                     '24:09:95',  # Huawei Technologies Co.,Ltd
                     '24:15:51',  # Huawei Device Co., Ltd.
                     '24:16:6D',  # Huawei Technologies Co.,Ltd
                     '24:1A:E6',  # Huawei Device Co., Ltd.
                     '24:1F:A0',  # Huawei Technologies Co.,Ltd
                     '24:26:D6',  # Huawei Technologies Co.,Ltd
                     '24:2E:02',  # Huawei Technologies Co.,Ltd
                     '24:30:F8',  # Huawei Device Co., Ltd.
                     '24:31:54',  # Huawei Technologies Co.,Ltd
                     '24:3F:AA',  # Huawei Device Co., Ltd.
                     '24:44:27',  # Huawei Technologies Co.,Ltd
                     '24:45:6B',  # Huawei Device Co., Ltd.
                     '24:46:E4',  # Huawei Technologies Co.,Ltd
                     '24:4B:F1',  # Huawei Technologies Co.,Ltd
                     '24:4C:07',  # Huawei Technologies Co.,Ltd
                     '24:5C:C5',  # Huawei Device Co., Ltd.
                     '24:5F:9F',  # Huawei Device Co., Ltd.
                     '24:64:9F',  # Huawei Device Co., Ltd.
                     '24:69:A5',  # Huawei Technologies Co.,Ltd
                     '24:6C:60',  # Huawei Device Co., Ltd.
                     '24:6F:8C',  # Huawei Device Co., Ltd.
                     '24:7F:3C',  # Huawei Technologies Co.,Ltd
                     '24:81:C7',  # Huawei Device Co., Ltd.
                     '24:91:BB',  # Huawei Technologies Co.,Ltd
                     '24:97:45',  # Huawei Technologies Co.,Ltd
                     '24:9E:AB',  # Huawei Technologies Co.,Ltd
                     '24:A4:87',  # Huawei Device Co., Ltd.
                     '24:A5:2C',  # Huawei Technologies Co.,Ltd
                     '24:A7:99',  # Huawei Device Co., Ltd.
                     '24:BC:F8',  # Huawei Technologies Co.,Ltd
                     '24:DA:33',  # Huawei Technologies Co.,Ltd
                     '24:DB:AC',  # Huawei Technologies Co.,Ltd
                     '24:DF:6A',  # Huawei Technologies Co.,Ltd
                     '24:E2:9D',  # Huawei Device Co., Ltd.
                     '24:E9:CA',  # Huawei Device Co., Ltd.
                     '24:EB:ED',  # Huawei Technologies Co.,Ltd
                     '24:F6:03',  # Huawei Technologies Co.,Ltd
                     '24:FB:65',  # Huawei Technologies Co.,Ltd
                     '28:11:EC',  # Huawei Technologies Co.,Ltd
                     '28:17:09',  # Huawei Technologies Co.,Ltd
                     '28:2B:96',  # Huawei Device Co., Ltd.
                     '28:31:52',  # Huawei Technologies Co.,Ltd
                     '28:31:F8',  # Huawei Technologies Co.,Ltd
                     '28:33:34',  # Huawei Device Co., Ltd.
                     '28:3C:E4',  # Huawei Technologies Co.,Ltd
                     '28:41:C6',  # Huawei Technologies Co.,Ltd
                     '28:41:EC',  # Huawei Technologies Co.,Ltd
                     '28:48:E7',  # Huawei Device Co., Ltd.
                     '28:4E:44',  # Huawei Technologies Co.,Ltd
                     '28:53:4E',  # Huawei Technologies Co.,Ltd
                     '28:54:71',  # Huawei Device Co., Ltd.
                     '28:5F:DB',  # Huawei Technologies Co.,Ltd
                     '28:64:B0',  # Huawei Device Co., Ltd.
                     '28:68:D2',  # Huawei Technologies Co.,Ltd
                     '28:6E:D4',  # Huawei Technologies Co.,Ltd
                     '28:80:8A',  # Huawei Technologies Co.,Ltd
                     '28:9E:97',  # Huawei Technologies Co.,Ltd
                     '28:A6:DB',  # Huawei Technologies Co.,Ltd
                     '28:B4:48',  # Huawei Technologies Co.,Ltd
                     '28:D3:EA',  # Huawei Device Co., Ltd.
                     '28:DE:E5',  # Huawei Technologies Co.,Ltd
                     '28:E3:4E',  # Huawei Technologies Co.,Ltd
                     '28:E5:B0',  # Huawei Technologies Co.,Ltd
                     '28:FB:AE',  # Huawei Technologies Co.,Ltd
                     '2C:07:86',  # Huawei Device Co., Ltd.
                     '2C:08:B4',  # Huawei Device Co., Ltd.
                     '2C:0B:AB',  # Huawei Technologies Co.,Ltd
                     '2C:15:D9',  # Huawei Technologies Co.,Ltd
                     '2C:1A:01',  # Huawei Technologies Co.,Ltd
                     '2C:20:80',  # Huawei Device Co., Ltd.
                     '2C:27:68',  # Huawei Technologies Co.,Ltd
                     '2C:3A:91',  # Huawei Device Co., Ltd.
                     '2C:52:AF',  # Huawei Technologies Co.,Ltd
                     '2C:55:D3',  # Huawei Technologies Co.,Ltd
                     '2C:58:E8',  # Huawei Technologies Co.,Ltd
                     '2C:69:3E',  # Huawei Technologies Co.,Ltd
                     '2C:78:0E',  # Huawei Device Co., Ltd.
                     '2C:94:52',  # Huawei Technologies Co.,Ltd
                     '2C:97:B1',  # Huawei Technologies Co.,Ltd
                     '2C:9D:1E',  # Huawei Technologies Co.,Ltd
                     '2C:A0:42',  # Huawei Device Co., Ltd.
                     '2C:A7:9E',  # Huawei Technologies Co.,Ltd
                     '2C:AB:00',  # Huawei Technologies Co.,Ltd
                     '2C:C5:46',  # Huawei Device Co., Ltd.
                     '2C:C8:F5',  # Huawei Device Co., Ltd.
                     '2C:CF:58',  # Huawei Technologies Co.,Ltd
                     '2C:ED:B0',  # Huawei Technologies Co.,Ltd
                     '2C:F2:95',  # Huawei Device Co., Ltd.
                     '30:19:84',  # Huawei Technologies Co.,Ltd
                     '30:35:C5',  # Huawei Device Co., Ltd.
                     '30:37:B3',  # Huawei Technologies Co.,Ltd
                     '30:45:96',  # Huawei Technologies Co.,Ltd
                     '30:49:9E',  # Huawei Technologies Co.,Ltd
                     '30:4E:1B',  # Huawei Device Co., Ltd.
                     '30:66:D0',  # Huawei Device Co., Ltd.
                     '30:74:96',  # Huawei Technologies Co.,Ltd
                     '30:7C:4A',  # Huawei Device Co., Ltd.
                     '30:87:30',  # Huawei Technologies Co.,Ltd
                     '30:8A:F7',  # Huawei Device Co., Ltd.
                     '30:8E:CF',  # Huawei Technologies Co.,Ltd
                     '30:96:10',  # Huawei Device Co., Ltd.
                     '30:96:3B',  # Huawei Device Co., Ltd.
                     '30:A1:FA',  # Huawei Technologies Co.,Ltd
                     '30:A2:C2',  # Huawei Device Co., Ltd.
                     '30:A9:98',  # Huawei Device Co., Ltd.
                     '30:AA:E4',  # Huawei Device Co., Ltd.
                     '30:C5:0F',  # Huawei Technologies Co.,Ltd
                     '30:D1:7E',  # Huawei Technologies Co.,Ltd
                     '30:E3:96',  # Huawei Device Co., Ltd.
                     '30:E9:8E',  # Huawei Technologies Co.,Ltd
                     '30:F3:35',  # Huawei Technologies Co.,Ltd
                     '30:FB:B8',  # Huawei Technologies Co.,Ltd
                     '30:FD:65',  # Huawei Technologies Co.,Ltd
                     '30:FF:FD',  # Huawei Technologies Co.,Ltd
                     '34:00:A3',  # Huawei Technologies Co.,Ltd
                     '34:0A:98',  # Huawei Technologies Co.,Ltd
                     '34:12:F9',  # Huawei Technologies Co.,Ltd
                     '34:1E:6B',  # Huawei Technologies Co.,Ltd
                     '34:29:12',  # Huawei Technologies Co.,Ltd
                     '34:2E:B6',  # Huawei Technologies Co.,Ltd
                     '34:46:EC',  # Huawei Device Co., Ltd.
                     '34:51:84',  # Huawei Device Co., Ltd.
                     '34:58:40',  # Huawei Technologies Co.,Ltd
                     '34:66:79',  # Huawei Technologies Co.,Ltd
                     '34:6A:C2',  # Huawei Technologies Co.,Ltd
                     '34:6B:D3',  # Huawei Technologies Co.,Ltd
                     '34:71:46',  # Huawei Device Co., Ltd.
                     '34:79:16',  # Huawei Technologies Co.,Ltd
                     '34:7E:00',  # Huawei Device Co., Ltd.
                     '34:A2:A2',  # Huawei Technologies Co.,Ltd
                     '34:B2:0A',  # Huawei Device Co., Ltd.
                     '34:B3:54',  # Huawei Technologies Co.,Ltd
                     '34:CD:BE',  # Huawei Technologies Co.,Ltd
                     '34:D6:93',  # Huawei Device Co., Ltd.
                     '38:0F:AD',  # Huawei Technologies Co.,Ltd
                     '38:20:28',  # Huawei Technologies Co.,Ltd
                     '38:22:F4',  # Huawei Device Co., Ltd.
                     '38:37:8B',  # Huawei Technologies Co.,Ltd
                     '38:39:6C',  # Huawei Device Co., Ltd.
                     '38:47:BC',  # Huawei Technologies Co.,Ltd
                     '38:4C:4F',  # Huawei Technologies Co.,Ltd
                     '38:52:47',  # Huawei Device Co., Ltd.
                     '38:88:1E',  # Huawei Technologies Co.,Ltd
                     '38:90:52',  # Huawei Technologies Co.,Ltd
                     '38:98:E9',  # Huawei Device Co., Ltd.
                     '38:A4:4B',  # Huawei Device Co., Ltd.
                     '38:B3:F7',  # Huawei Device Co., Ltd.
                     '38:BC:01',  # Huawei Technologies Co.,Ltd
                     '38:EB:47',  # Huawei Technologies Co.,Ltd
                     '38:F7:F1',  # Huawei Device Co., Ltd.
                     '38:F8:89',  # Huawei Technologies Co.,Ltd
                     '38:FB:14',  # Huawei Technologies Co.,Ltd
                     '38:FC:34',  # Huawei Device Co., Ltd.
                     '3A:72:C2',  # Huawei Technologies Co.,Ltd
                     '3C:05:8E',  # Huawei Technologies Co.,Ltd
                     '3C:13:BB',  # Huawei Technologies Co.,Ltd
                     '3C:15:FB',  # Huawei Technologies Co.,Ltd
                     '3C:30:6F',  # Huawei Technologies Co.,Ltd
                     '3C:47:11',  # Huawei Technologies Co.,Ltd
                     '3C:54:47',  # Huawei Technologies Co.,Ltd
                     '3C:67:8C',  # Huawei Technologies Co.,Ltd
                     '3C:78:43',  # Huawei Technologies Co.,Ltd
                     '3C:86:9A',  # Huawei Technologies Co.,Ltd
                     '3C:93:F4',  # Huawei Technologies Co.,Ltd
                     '3C:9B:C6',  # Huawei Device Co., Ltd.
                     '3C:9D:56',  # Huawei Technologies Co.,Ltd
                     '3C:A1:61',  # Huawei Technologies Co.,Ltd
                     '3C:A3:7E',  # Huawei Technologies Co.,Ltd
                     '3C:A9:16',  # Huawei Device Co., Ltd.
                     '3C:B2:33',  # Huawei Device Co., Ltd.
                     '3C:C0:3E',  # Huawei Technologies Co.,Ltd
                     '3C:CD:5D',  # Huawei Technologies Co.,Ltd
                     '3C:DF:BD',  # Huawei Technologies Co.,Ltd
                     '3C:E8:24',  # Huawei Technologies Co.,Ltd
                     '3C:F6:92',  # Huawei Device Co., Ltd.
                     '3C:F8:08',  # Huawei Technologies Co.,Ltd
                     '3C:FA:43',  # Huawei Technologies Co.,Ltd
                     '3C:FF:D8',  # Huawei Technologies Co.,Ltd
                     '40:06:34',  # Huawei Device Co., Ltd.
                     '40:14:AD',  # Huawei Device Co., Ltd.
                     '40:3B:7B',  # Huawei Device Co., Ltd.
                     '40:41:0D',  # Huawei Technologies Co.,Ltd
                     '40:45:C4',  # Huawei Technologies Co.,Ltd
                     '40:4D:8E',  # Huawei Technologies Co.,Ltd
                     '40:4F:42',  # Huawei Technologies Co.,Ltd
                     '40:76:A9',  # Huawei Device Co., Ltd.
                     '40:7D:0F',  # Huawei Technologies Co.,Ltd
                     '40:8E:DF',  # Huawei Device Co., Ltd.
                     '40:B1:5C',  # Huawei Technologies Co.,Ltd
                     '40:B6:E7',  # Huawei Device Co., Ltd.
                     '40:B7:0E',  # Huawei Device Co., Ltd.
                     '40:C3:BC',  # Huawei Device Co., Ltd.
                     '40:CB:A8',  # Huawei Technologies Co.,Ltd
                     '40:DC:A5',  # Huawei Device Co., Ltd.
                     '40:EE:DD',  # Huawei Technologies Co.,Ltd
                     '44:00:4D',  # Huawei Technologies Co.,Ltd
                     '44:22:7C',  # Huawei Technologies Co.,Ltd
                     '44:27:2E',  # Huawei Device Co., Ltd.
                     '44:30:3F',  # Huawei Technologies Co.,Ltd
                     '44:55:B1',  # Huawei Technologies Co.,Ltd
                     '44:55:C4',  # Huawei Device Co., Ltd.
                     '44:59:E3',  # Huawei Technologies Co.,Ltd
                     '44:67:47',  # Huawei Technologies Co.,Ltd
                     '44:6A:2E',  # Huawei Technologies Co.,Ltd
                     '44:6E:E5',  # Huawei Technologies Co.,Ltd
                     '44:76:54',  # Huawei Technologies Co.,Ltd
                     '44:82:E5',  # Huawei Technologies Co.,Ltd
                     '44:9B:C1',  # Huawei Technologies Co.,Ltd
                     '44:9F:46',  # Huawei Device Co., Ltd.
                     '44:A0:38',  # Huawei Device Co., Ltd.
                     '44:A1:91',  # Huawei Technologies Co.,Ltd
                     '44:AE:44',  # Huawei Device Co., Ltd.
                     '44:C3:46',  # Huawei Technologies Co.,Ltd
                     '44:C3:B6',  # Huawei Technologies Co.,Ltd
                     '44:C7:FC',  # Huawei Device Co., Ltd.
                     '44:D7:91',  # Huawei Technologies Co.,Ltd
                     '44:E9:68',  # Huawei Technologies Co.,Ltd
                     '48:00:31',  # Huawei Technologies Co.,Ltd
                     '48:05:E2',  # Huawei Device Co., Ltd.
                     '48:12:58',  # Huawei Technologies Co.,Ltd
                     '48:12:8F',  # Huawei Technologies Co.,Ltd
                     '48:25:F3',  # Huawei Device Co., Ltd.
                     '48:27:C5',  # Huawei Technologies Co.,Ltd
                     '48:2C:D0',  # Huawei Technologies Co.,Ltd
                     '48:2F:D7',  # Huawei Technologies Co.,Ltd
                     '48:31:DB',  # Huawei Device Co., Ltd.
                     '48:38:71',  # Huawei Device Co., Ltd.
                     '48:3C:0C',  # Huawei Technologies Co.,Ltd
                     '48:3F:E9',  # Huawei Technologies Co.,Ltd
                     '48:43:5A',  # Huawei Technologies Co.,Ltd
                     '48:46:FB',  # Huawei Technologies Co.,Ltd
                     '48:47:4B',  # Huawei Device Co., Ltd.
                     '48:4C:29',  # Huawei Technologies Co.,Ltd
                     '48:4C:86',  # Huawei Device Co., Ltd.
                     '48:57:02',  # Huawei Technologies Co.,Ltd
                     '48:62:76',  # Huawei Technologies Co.,Ltd
                     '48:63:45',  # Huawei Device Co., Ltd.
                     '48:70:6F',  # Huawei Technologies Co.,Ltd
                     '48:7B:6B',  # Huawei Technologies Co.,Ltd
                     '48:8C:63',  # Huawei Device Co., Ltd.
                     '48:8E:EF',  # Huawei Technologies Co.,Ltd
                     '48:A5:16',  # Huawei Device Co., Ltd.
                     '48:AD:08',  # Huawei Technologies Co.,Ltd
                     '48:B2:5D',  # Huawei Technologies Co.,Ltd
                     '48:BD:4A',  # Huawei Technologies Co.,Ltd
                     '48:CD:D3',  # Huawei Technologies Co.,Ltd
                     '48:D5:39',  # Huawei Technologies Co.,Ltd
                     '48:DB:50',  # Huawei Technologies Co.,Ltd
                     '48:DC:2D',  # Huawei Technologies Co.,Ltd
                     '48:EF:61',  # Huawei Device Co., Ltd.
                     '48:F8:DB',  # Huawei Technologies Co.,Ltd
                     '48:FD:8E',  # Huawei Technologies Co.,Ltd
                     '4C:1F:CC',  # Huawei Technologies Co.,Ltd
                     '4C:2F:D7',  # Huawei Device Co., Ltd.
                     '4C:50:77',  # Huawei Device Co., Ltd.
                     '4C:54:99',  # Huawei Technologies Co.,Ltd
                     '4C:61:7E',  # Huawei Device Co., Ltd.
                     '4C:63:AD',  # Huawei Device Co., Ltd.
                     '4C:88:9E',  # Huawei Device Co., Ltd.
                     '4C:8B:EF',  # Huawei Technologies Co.,Ltd
                     '4C:8D:53',  # Huawei Technologies Co.,Ltd
                     '4C:AE:13',  # Huawei Technologies Co.,Ltd
                     '4C:B0:87',  # Huawei Technologies Co.,Ltd
                     '4C:B1:6C',  # Huawei Technologies Co.,Ltd
                     '4C:D0:CB',  # Huawei Technologies Co.,Ltd
                     '4C:D0:DD',  # Huawei Technologies Co.,Ltd
                     '4C:D1:A1',  # Huawei Technologies Co.,Ltd
                     '4C:D6:29',  # Huawei Technologies Co.,Ltd
                     '4C:F5:5B',  # Huawei Technologies Co.,Ltd
                     '4C:F9:5D',  # Huawei Technologies Co.,Ltd
                     '4C:FB:45',  # Huawei Technologies Co.,Ltd
                     '50:01:6B',  # Huawei Technologies Co.,Ltd
                     '50:01:D9',  # Huawei Technologies Co.,Ltd
                     '50:04:B8',  # Huawei Technologies Co.,Ltd
                     '50:0B:26',  # Huawei Technologies Co.,Ltd
                     '50:14:C1',  # Huawei Technologies Co.,Ltd
                     '50:1D:93',  # Huawei Technologies Co.,Ltd
                     '50:21:EC',  # Huawei Device Co., Ltd.
                     '50:28:73',  # Huawei Device Co., Ltd.
                     '50:3F:50',  # Huawei Device Co., Ltd.
                     '50:41:72',  # Huawei Technologies Co.,Ltd
                     '50:46:4A',  # Huawei Technologies Co.,Ltd
                     '50:4B:9E',  # Huawei Device Co., Ltd.
                     '50:58:6F',  # Huawei Device Co., Ltd.
                     '50:5D:AC',  # Huawei Technologies Co.,Ltd
                     '50:63:91',  # Huawei Technologies Co.,Ltd
                     '50:66:E5',  # Huawei Device Co., Ltd.
                     '50:68:0A',  # Huawei Technologies Co.,Ltd
                     '50:68:AC',  # Huawei Device Co., Ltd.
                     '50:6F:77',  # Huawei Technologies Co.,Ltd
                     '50:78:B0',  # Huawei Device Co., Ltd.
                     '50:89:D1',  # Huawei Device Co., Ltd.
                     '50:9A:88',  # Huawei Technologies Co.,Ltd
                     '50:9F:27',  # Huawei Technologies Co.,Ltd
                     '50:A1:F3',  # Huawei Device Co., Ltd.
                     '50:A7:2B',  # Huawei Technologies Co.,Ltd
                     '50:F7:ED',  # Huawei Device Co., Ltd.
                     '50:F9:58',  # Huawei Device Co., Ltd.
                     '54:02:95',  # Huawei Technologies Co.,Ltd
                     '54:07:64',  # Huawei Device Co., Ltd.
                     '54:0D:F9',  # Huawei Device Co., Ltd.
                     '54:10:2E',  # Huawei Technologies Co.,Ltd
                     '54:12:CB',  # Huawei Technologies Co.,Ltd
                     '54:13:10',  # Huawei Technologies Co.,Ltd
                     '54:21:1D',  # Huawei Device Co., Ltd.
                     '54:22:59',  # Huawei Technologies Co.,Ltd
                     '54:25:EA',  # Huawei Technologies Co.,Ltd
                     '54:34:EF',  # Huawei Technologies Co.,Ltd
                     '54:39:DF',  # Huawei Technologies Co.,Ltd
                     '54:44:3B',  # Huawei Technologies Co.,Ltd
                     '54:51:1B',  # Huawei Technologies Co.,Ltd
                     '54:52:84',  # Huawei Device Co., Ltd.
                     '54:55:D5',  # Huawei Device Co., Ltd.
                     '54:69:90',  # Huawei Technologies Co.,Ltd
                     '54:71:DD',  # Huawei Device Co., Ltd.
                     '54:89:98',  # Huawei Technologies Co.,Ltd
                     '54:92:09',  # Huawei Technologies Co.,Ltd
                     '54:A5:1B',  # Huawei Technologies Co.,Ltd
                     '54:A6:DB',  # Huawei Device Co., Ltd.
                     '54:B1:21',  # Huawei Technologies Co.,Ltd
                     '54:BA:D6',  # Huawei Technologies Co.,Ltd
                     '54:C4:80',  # Huawei Technologies Co.,Ltd
                     '54:CF:8D',  # Huawei Technologies Co.,Ltd
                     '54:D9:C6',  # Huawei Device Co., Ltd.
                     '54:E1:5B',  # Huawei Device Co., Ltd.
                     '54:EF:43',  # Huawei Technologies Co.,Ltd
                     '54:F2:94',  # Huawei Device Co., Ltd.
                     '54:F6:07',  # Huawei Device Co., Ltd.
                     '54:F6:E2',  # Huawei Technologies Co.,Ltd
                     '58:1F:28',  # Huawei Technologies Co.,Ltd
                     '58:25:75',  # Huawei Technologies Co.,Ltd
                     '58:2A:F7',  # Huawei Technologies Co.,Ltd
                     '58:35:5D',  # Huawei Device Co., Ltd.
                     '58:56:C2',  # Huawei Technologies Co.,Ltd
                     '58:60:5F',  # Huawei Technologies Co.,Ltd
                     '58:73:D1',  # Huawei Technologies Co.,Ltd
                     '58:7F:66',  # Huawei Technologies Co.,Ltd
                     '58:87:9F',  # Huawei Device Co., Ltd.
                     '58:93:51',  # Huawei Device Co., Ltd.
                     '58:94:AE',  # Huawei Device Co., Ltd.
                     '58:95:7E',  # Huawei Device Co., Ltd.
                     '58:AE:2B',  # Huawei Device Co., Ltd.
                     '58:AE:A8',  # Huawei Technologies Co.,Ltd
                     '58:BA:D4',  # Huawei Technologies Co.,Ltd
                     '58:BE:72',  # Huawei Technologies Co.,Ltd
                     '58:D0:61',  # Huawei Technologies Co.,Ltd
                     '58:D7:59',  # Huawei Technologies Co.,Ltd
                     '58:F2:FC',  # Huawei Device Co., Ltd.
                     '58:F8:D7',  # Huawei Technologies Co.,Ltd
                     '58:F9:87',  # Huawei Technologies Co.,Ltd
                     '5C:03:39',  # Huawei Technologies Co.,Ltd
                     '5C:07:A6',  # Huawei Technologies Co.,Ltd
                     '5C:09:79',  # Huawei Technologies Co.,Ltd
                     '5C:16:7D',  # Huawei Technologies Co.,Ltd
                     '5C:17:20',  # Huawei Device Co., Ltd.
                     '5C:4C:A9',  # Huawei Technologies Co.,Ltd
                     '5C:54:6D',  # Huawei Technologies Co.,Ltd
                     '5C:64:7A',  # Huawei Technologies Co.,Ltd
                     '5C:70:75',  # Huawei Technologies Co.,Ltd
                     '5C:78:F8',  # Huawei Device Co., Ltd.
                     '5C:7D:5E',  # Huawei Technologies Co.,Ltd
                     '5C:91:57',  # Huawei Technologies Co.,Ltd
                     '5C:9A:A1',  # Huawei Device Co., Ltd.
                     '5C:A8:6A',  # Huawei Technologies Co.,Ltd
                     '5C:B0:0A',  # Huawei Technologies Co.,Ltd
                     '5C:B3:95',  # Huawei Technologies Co.,Ltd
                     '5C:B4:3E',  # Huawei Technologies Co.,Ltd
                     '5C:BD:9A',  # Huawei Device Co., Ltd.
                     '5C:C0:A0',  # Huawei Technologies Co.,Ltd
                     '5C:C3:07',  # Huawei Technologies Co.,Ltd
                     '5C:C7:87',  # Huawei Device Co., Ltd.
                     '5C:D8:9E',  # Huawei Device Co., Ltd.
                     '5C:E7:47',  # Huawei Technologies Co.,Ltd
                     '5C:E8:83',  # Huawei Technologies Co.,Ltd
                     '5C:F9:6A',  # Huawei Technologies Co.,Ltd
                     '60:01:B1',  # Huawei Technologies Co.,Ltd
                     '60:08:10',  # Huawei Technologies Co.,Ltd
                     '60:10:9E',  # Huawei Technologies Co.,Ltd
                     '60:12:3C',  # Huawei Technologies Co.,Ltd
                     '60:18:3A',  # Huawei Device Co., Ltd.
                     '60:2E:20',  # Huawei Technologies Co.,Ltd
                     '60:3D:29',  # Huawei Technologies Co.,Ltd
                     '60:4D:E1',  # Huawei Technologies Co.,Ltd
                     '60:4F:5B',  # Huawei Device Co., Ltd.
                     '60:53:75',  # Huawei Technologies Co.,Ltd
                     '60:5E:4F',  # Huawei Device Co., Ltd.
                     '60:7E:CD',  # Huawei Technologies Co.,Ltd
                     '60:83:34',  # Huawei Technologies Co.,Ltd
                     '60:96:A4',  # Huawei Technologies Co.,Ltd
                     '60:9B:B4',  # Huawei Technologies Co.,Ltd
                     '60:A2:C6',  # Huawei Technologies Co.,Ltd
                     '60:A6:C5',  # Huawei Technologies Co.,Ltd
                     '60:A7:51',  # Huawei Device Co., Ltd.
                     '60:AA:EF',  # Huawei Device Co., Ltd.
                     '60:CE:41',  # Huawei Technologies Co.,Ltd
                     '60:D7:55',  # Huawei Technologies Co.,Ltd
                     '60:DE:44',  # Huawei Technologies Co.,Ltd
                     '60:DE:F3',  # Huawei Technologies Co.,Ltd
                     '60:E7:01',  # Huawei Technologies Co.,Ltd
                     '60:F1:8A',  # Huawei Technologies Co.,Ltd
                     '60:FA:9D',  # Huawei Technologies Co.,Ltd
                     '64:13:AB',  # Huawei Technologies Co.,Ltd
                     '64:16:F0',  # Huawei Technologies Co.,Ltd
                     '64:23:15',  # Huawei Device Co., Ltd.
                     '64:27:53',  # Huawei Device Co., Ltd.
                     '64:2C:AC',  # Huawei Technologies Co.,Ltd
                     '64:3E:0A',  # Huawei Technologies Co.,Ltd
                     '64:3E:8C',  # Huawei Technologies Co.,Ltd
                     '64:51:F4',  # Huawei Device Co., Ltd.
                     '64:5E:10',  # Huawei Technologies Co.,Ltd
                     '64:61:40',  # Huawei Device Co., Ltd.
                     '64:67:CD',  # Huawei Technologies Co.,Ltd
                     '64:6D:4E',  # Huawei Technologies Co.,Ltd
                     '64:6D:6C',  # Huawei Technologies Co.,Ltd
                     '64:79:24',  # Huawei Device Co., Ltd.
                     '64:A1:98',  # Huawei Device Co., Ltd.
                     '64:A2:8A',  # Huawei Device Co., Ltd.
                     '64:A6:51',  # Huawei Technologies Co.,Ltd
                     '64:B0:E8',  # Huawei Device Co., Ltd.
                     '64:BF:6B',  # Huawei Technologies Co.,Ltd
                     '64:C3:94',  # Huawei Technologies Co.,Ltd
                     '64:D7:C0',  # Huawei Device Co., Ltd.
                     '64:F7:05',  # Huawei Device Co., Ltd.
                     '64:F8:1C',  # Huawei Technologies Co., Ltd.
                     '68:13:24',  # Huawei Device Co., Ltd.
                     '68:1B:EF',  # Huawei Technologies Co.,Ltd
                     '68:45:71',  # Huawei Device Co., Ltd.
                     '68:4A:AE',  # Huawei Technologies Co.,Ltd
                     '68:63:72',  # Huawei Device Co., Ltd.
                     '68:81:E0',  # Huawei Technologies Co.,Ltd
                     '68:89:C1',  # Huawei Technologies Co.,Ltd
                     '68:8F:84',  # Huawei Technologies Co.,Ltd
                     '68:96:2E',  # Huawei Technologies Co.,Ltd
                     '68:9E:6A',  # Huawei Device Co., Ltd.
                     '68:A0:3E',  # Huawei Technologies Co.,Ltd
                     '68:A0:F6',  # Huawei Technologies Co.,Ltd
                     '68:A4:6A',  # Huawei Technologies Co.,Ltd
                     '68:A8:28',  # Huawei Technologies Co.,Ltd
                     '68:CC:6E',  # Huawei Technologies Co.,Ltd
                     '68:D9:27',  # Huawei Technologies Co.,Ltd
                     '68:E2:09',  # Huawei Technologies Co.,Ltd
                     '68:F5:43',  # Huawei Technologies Co.,Ltd
                     '6C:04:7A',  # Huawei Technologies Co.,Ltd
                     '6C:06:D6',  # Huawei Device Co., Ltd.
                     '6C:14:6E',  # Huawei Technologies Co.,Ltd
                     '6C:16:32',  # Huawei Technologies Co.,Ltd
                     '6C:1A:75',  # Huawei Device Co., Ltd.
                     '6C:26:36',  # Huawei Technologies Co.,Ltd
                     '6C:34:91',  # Huawei Technologies Co.,Ltd
                     '6C:44:2A',  # Huawei Technologies Co.,Ltd
                     '6C:51:BF',  # Huawei Device Co., Ltd.
                     '6C:51:E4',  # Huawei Device Co., Ltd.
                     '6C:55:8D',  # Huawei Technologies Co.,Ltd
                     '6C:60:D0',  # Huawei Device Co., Ltd.
                     '6C:67:EF',  # Huawei Technologies Co.,Ltd
                     '6C:6C:0F',  # Huawei Technologies Co.,Ltd
                     '6C:71:D2',  # Huawei Technologies Co.,Ltd
                     '6C:76:37',  # Huawei Device Co., Ltd.
                     '6C:B4:FD',  # Huawei Device Co., Ltd.
                     '6C:B7:49',  # Huawei Technologies Co.,Ltd
                     '6C:B7:E2',  # Huawei Technologies Co.,Ltd
                     '6C:D1:E5',  # Huawei Technologies Co.,Ltd
                     '6C:D6:3F',  # Huawei Technologies Co.,Ltd
                     '6C:D7:04',  # Huawei Technologies Co.,Ltd
                     '6C:E8:74',  # Huawei Technologies Co.,Ltd
                     '6C:EB:B6',  # Huawei Technologies Co.,Ltd
                     '70:19:2F',  # Huawei Technologies Co.,Ltd
                     '70:2F:35',  # Huawei Technologies Co.,Ltd
                     '70:40:FF',  # Huawei Device Co., Ltd.
                     '70:46:98',  # Huawei Technologies Co.,Ltd
                     '70:4E:6B',  # Huawei Technologies Co.,Ltd
                     '70:54:F5',  # Huawei Technologies Co.,Ltd
                     '70:66:B9',  # Huawei Device Co., Ltd.
                     '70:72:3C',  # Huawei Technologies Co.,Ltd
                     '70:79:90',  # Huawei Technologies Co.,Ltd
                     '70:7B:E8',  # Huawei Technologies Co.,Ltd
                     '70:7C:E3',  # Huawei Technologies Co.,Ltd
                     '70:8A:09',  # Huawei Technologies Co.,Ltd
                     '70:8C:B6',  # Huawei Technologies Co.,Ltd
                     '70:90:B7',  # Huawei Device Co., Ltd.
                     '70:9C:45',  # Huawei Technologies Co.,Ltd
                     '70:A8:E3',  # Huawei Technologies Co.,Ltd
                     '70:C7:F2',  # Huawei Technologies Co.,Ltd
                     '70:D3:13',  # Huawei Technologies Co.,Ltd
                     '70:DD:EF',  # Huawei Device Co., Ltd.
                     '70:FD:45',  # Huawei Technologies Co.,Ltd
                     '74:0A:E1',  # Huawei Device Co., Ltd.
                     '74:0C:EE',  # Huawei Device Co., Ltd.
                     '74:22:BB',  # Huawei Device Co., Ltd.
                     '74:34:2B',  # Huawei Technologies Co.,Ltd
                     '74:45:2D',  # Huawei Device Co., Ltd.
                     '74:4D:6D',  # Huawei Technologies Co.,Ltd
                     '74:59:09',  # Huawei Technologies Co.,Ltd
                     '74:5A:AA',  # Huawei Technologies Co.,Ltd
                     '74:60:FA',  # Huawei Technologies Co.,Ltd
                     '74:63:C2',  # Huawei Device Co., Ltd.
                     '74:70:69',  # Huawei Device Co., Ltd.
                     '74:87:2E',  # Huawei Technologies Co.,Ltd
                     '74:88:2A',  # Huawei Technologies Co.,Ltd
                     '74:9B:89',  # Huawei Technologies Co.,Ltd
                     '74:9D:8F',  # Huawei Technologies Co.,Ltd
                     '74:A0:63',  # Huawei Technologies Co.,Ltd
                     '74:A5:28',  # Huawei Technologies Co.,Ltd
                     '74:B7:25',  # Huawei Device Co., Ltd.
                     '74:C1:4F',  # Huawei Technologies Co.,Ltd
                     '74:D2:1D',  # Huawei Technologies Co.,Ltd
                     '74:D6:E5',  # Huawei Device Co., Ltd.
                     '74:E9:BF',  # Huawei Technologies Co.,Ltd
                     '78:04:E3',  # Huawei Device Co., Ltd.
                     '78:06:C9',  # Huawei Device Co., Ltd.
                     '78:08:4D',  # Huawei Technologies Co.,Ltd
                     '78:16:99',  # Huawei Technologies Co.,Ltd
                     '78:17:BE',  # Huawei Technologies Co.,Ltd
                     '78:18:A8',  # Huawei Device Co., Ltd.
                     '78:1D:BA',  # Huawei Technologies Co.,Ltd
                     '78:2D:AD',  # Huawei Technologies Co.,Ltd
                     '78:45:B3',  # Huawei Device Co., Ltd.
                     '78:57:73',  # Huawei Technologies Co.,Ltd
                     '78:58:60',  # Huawei Technologies Co.,Ltd
                     '78:5B:64',  # Huawei Device Co., Ltd.
                     '78:5C:5E',  # Huawei Technologies Co.,Ltd
                     '78:62:56',  # Huawei Technologies Co.,Ltd
                     '78:6A:89',  # Huawei Technologies Co.,Ltd
                     '78:85:F4',  # Huawei Device Co., Ltd.
                     '78:9F:AA',  # Huawei Device Co., Ltd.
                     '78:B4:6A',  # Huawei Technologies Co.,Ltd
                     '78:B5:54',  # Huawei Device Co., Ltd.
                     '78:C5:F8',  # Huawei Device Co., Ltd.
                     '78:CF:2F',  # Huawei Technologies Co.,Ltd
                     '78:CF:F9',  # Huawei Device Co., Ltd.
                     '78:D7:52',  # Huawei Technologies Co.,Ltd
                     '78:DD:33',  # Huawei Technologies Co.,Ltd
                     '78:E2:2C',  # Huawei Device Co., Ltd.
                     '78:EB:46',  # Huawei Technologies Co.,Ltd
                     '78:F0:9B',  # Huawei Device Co., Ltd.
                     '78:F5:57',  # Huawei Technologies Co.,Ltd
                     '78:F5:FD',  # Huawei Technologies Co.,Ltd
                     '7C:00:4D',  # Huawei Technologies Co.,Ltd
                     '7C:11:CB',  # Huawei Technologies Co.,Ltd
                     '7C:1A:C0',  # Huawei Technologies Co.,Ltd
                     '7C:1B:93',  # Huawei Device Co., Ltd.
                     '7C:1C:F1',  # Huawei Technologies Co.,Ltd
                     '7C:33:F9',  # Huawei Technologies Co.,Ltd
                     '7C:39:85',  # Huawei Technologies Co.,Ltd
                     '7C:3D:2B',  # Huawei Device Co., Ltd.
                     '7C:3E:74',  # Huawei Device Co., Ltd.
                     '7C:60:97',  # Huawei Technologies Co.,Ltd
                     '7C:66:9A',  # Huawei Technologies Co.,Ltd
                     '7C:73:EB',  # Huawei Device Co., Ltd.
                     '7C:76:68',  # Huawei Technologies Co.,Ltd
                     '7C:7D:3D',  # Huawei Technologies Co.,Ltd
                     '7C:89:31',  # Huawei Device Co., Ltd.
                     '7C:94:2A',  # Huawei Technologies Co.,Ltd
                     '7C:97:E1',  # Huawei Device Co., Ltd.
                     '7C:A1:77',  # Huawei Technologies Co.,Ltd
                     '7C:A2:3E',  # Huawei Technologies Co.,Ltd
                     '7C:B1:5D',  # Huawei Technologies Co.,Ltd
                     '7C:C3:85',  # Huawei Technologies Co.,Ltd
                     '7C:D9:A0',  # Huawei Technologies Co.,Ltd
                     '80:13:82',  # Huawei Technologies Co.,Ltd
                     '80:2E:C3',  # Huawei Technologies Co.,Ltd
                     '80:38:BC',  # Huawei Technologies Co.,Ltd
                     '80:3C:20',  # Huawei Technologies Co.,Ltd
                     '80:41:26',  # Huawei Technologies Co.,Ltd
                     '80:54:D9',  # Huawei Technologies Co.,Ltd
                     '80:60:36',  # Huawei Technologies Co.,Ltd
                     '80:69:33',  # Huawei Technologies Co.,Ltd
                     '80:6F:1C',  # Huawei Device Co., Ltd.
                     '80:71:7A',  # Huawei Technologies Co.,Ltd
                     '80:72:64',  # Huawei Device Co., Ltd.
                     '80:7D:14',  # Huawei Technologies Co.,Ltd
                     '80:B5:75',  # Huawei Technologies Co.,Ltd
                     '80:B6:86',  # Huawei Technologies Co.,Ltd
                     '80:CC:12',  # Huawei Device Co., Ltd.
                     '80:CF:A2',  # Huawei Device Co., Ltd.
                     '80:D0:9B',  # Huawei Technologies Co.,Ltd
                     '80:D4:A5',  # Huawei Technologies Co.,Ltd
                     '80:E1:BF',  # Huawei Technologies Co.,Ltd
                     '80:F1:A4',  # Huawei Technologies Co.,Ltd
                     '80:FB:06',  # Huawei Technologies Co.,Ltd
                     '84:15:D3',  # Huawei Technologies Co.,Ltd
                     '84:21:F1',  # Huawei Technologies Co.,Ltd
                     '84:3E:92',  # Huawei Technologies Co.,Ltd
                     '84:46:FE',  # Huawei Technologies Co.,Ltd
                     '84:47:65',  # Huawei Technologies Co.,Ltd
                     '84:50:75',  # Huawei Device Co., Ltd.
                     '84:54:DF',  # Huawei Device Co., Ltd.
                     '84:5B:12',  # Huawei Technologies Co.,Ltd
                     '84:64:DD',  # Huawei Technologies Co.,Ltd
                     '84:71:6A',  # Huawei Device Co., Ltd.
                     '84:76:37',  # Huawei Technologies Co.,Ltd
                     '84:93:A0',  # Huawei Device Co., Ltd.
                     '84:9F:B5',  # Huawei Technologies Co.,Ltd
                     '84:A8:E4',  # Huawei Technologies Co.,Ltd
                     '84:A9:C4',  # Huawei Technologies Co.,Ltd
                     '84:AD:58',  # Huawei Technologies Co.,Ltd
                     '84:BE:52',  # Huawei Technologies Co.,Ltd
                     '84:CC:63',  # Huawei Device Co., Ltd.
                     '84:D3:D5',  # Huawei Device Co., Ltd.
                     '84:DB:A4',  # Huawei Device Co., Ltd.
                     '84:DB:AC',  # Huawei Technologies Co.,Ltd
                     '84:E9:86',  # Huawei Device Co., Ltd.
                     '88:10:8F',  # Huawei Technologies Co.,Ltd
                     '88:11:96',  # Huawei Technologies Co.,Ltd
                     '88:15:C5',  # Huawei Device Co., Ltd.
                     '88:28:B3',  # Huawei Technologies Co.,Ltd
                     '88:36:CF',  # Huawei Device Co., Ltd.
                     '88:3F:27',  # Huawei Device Co., Ltd.
                     '88:3F:D3',  # Huawei Technologies Co.,Ltd
                     '88:40:33',  # Huawei Technologies Co.,Ltd
                     '88:40:3B',  # Huawei Technologies Co.,Ltd
                     '88:44:77',  # Huawei Technologies Co.,Ltd
                     '88:53:D4',  # Huawei Technologies Co.,Ltd
                     '88:66:39',  # Huawei Technologies Co.,Ltd
                     '88:67:DC',  # Huawei Technologies Co.,Ltd
                     '88:69:3D',  # Huawei Technologies Co.,Ltd
                     '88:6D:2D',  # Huawei Device Co., Ltd.
                     '88:6E:EB',  # Huawei Technologies Co.,Ltd
                     '88:74:77',  # Huawei Technologies Co.,Ltd
                     '88:81:B9',  # Huawei Device Co., Ltd.
                     '88:86:03',  # Huawei Technologies Co.,Ltd
                     '88:89:2F',  # Huawei Technologies Co.,Ltd
                     '88:8E:68',  # Huawei Device Co., Ltd.
                     '88:8F:A4',  # Huawei Device Co., Ltd.
                     '88:A0:BE',  # Huawei Technologies Co.,Ltd
                     '88:A2:D7',  # Huawei Technologies Co.,Ltd
                     '88:B4:BE',  # Huawei Technologies Co.,Ltd
                     '88:BC:C1',  # Huawei Technologies Co.,Ltd
                     '88:BF:E4',  # Huawei Technologies Co.,Ltd
                     '88:C2:27',  # Huawei Technologies Co.,Ltd
                     '88:C6:E8',  # Huawei Technologies Co.,Ltd
                     '88:CE:3F',  # Huawei Technologies Co.,Ltd
                     '88:CE:FA',  # Huawei Technologies Co.,Ltd
                     '88:CF:98',  # Huawei Technologies Co.,Ltd
                     '88:E0:56',  # Huawei Technologies Co.,Ltd
                     '88:E3:AB',  # Huawei Technologies Co.,Ltd
                     '88:F5:6E',  # Huawei Technologies Co.,Ltd
                     '88:F8:72',  # Huawei Technologies Co.,Ltd
                     '8C:0D:76',  # Huawei Technologies Co.,Ltd
                     '8C:0F:C9',  # Huawei Device Co., Ltd.
                     '8C:15:C7',  # Huawei Technologies Co.,Ltd
                     '8C:17:B6',  # Huawei Device Co., Ltd.
                     '8C:25:05',  # Huawei Technologies Co.,Ltd
                     '8C:34:46',  # Huawei Device Co., Ltd.
                     '8C:34:FD',  # Huawei Technologies Co.,Ltd
                     '8C:42:6D',  # Huawei Technologies Co.,Ltd
                     '8C:5A:C1',  # Huawei Device Co., Ltd.
                     '8C:5E:BD',  # Huawei Device Co., Ltd.
                     '8C:68:3A',  # Huawei Technologies Co.,Ltd
                     '8C:6B:DB',  # Huawei Device Co., Ltd.
                     '8C:6D:77',  # Huawei Technologies Co.,Ltd
                     '8C:83:E8',  # Huawei Technologies Co.,Ltd
                     '8C:E5:EF',  # Huawei Technologies Co.,Ltd
                     '8C:EB:C6',  # Huawei Technologies Co.,Ltd
                     '8C:FA:DD',  # Huawei Technologies Co.,Ltd
                     '8C:FD:18',  # Huawei Technologies Co.,Ltd
                     '90:01:17',  # Huawei Technologies Co.,Ltd
                     '90:03:25',  # Huawei Technologies Co.,Ltd
                     '90:16:BA',  # Huawei Technologies Co.,Ltd
                     '90:17:3F',  # Huawei Technologies Co.,Ltd
                     '90:17:AC',  # Huawei Technologies Co.,Ltd
                     '90:17:C8',  # Huawei Technologies Co.,Ltd
                     '90:25:F2',  # Huawei Technologies Co.,Ltd
                     '90:2B:D2',  # Huawei Technologies Co.,Ltd
                     '90:3F:EA',  # Huawei Technologies Co.,Ltd
                     '90:4E:2B',  # Huawei Technologies Co.,Ltd
                     '90:5E:44',  # Huawei Technologies Co.,Ltd
                     '90:64:AD',  # Huawei Technologies Co.,Ltd
                     '90:67:1C',  # Huawei Technologies Co.,Ltd
                     '90:80:8F',  # Huawei Device Co., Ltd.
                     '90:94:97',  # Huawei Technologies Co.,Ltd
                     '90:98:38',  # Huawei Device Co., Ltd.
                     '90:A5:7D',  # Huawei Device Co., Ltd.
                     '90:A5:AF',  # Huawei Technologies Co.,Ltd
                     '90:CC:7A',  # Huawei Device Co., Ltd.
                     '90:F6:44',  # Huawei Device Co., Ltd.
                     '90:F9:70',  # Huawei Technologies Co.,Ltd
                     '90:F9:B7',  # Huawei Technologies Co.,Ltd
                     '94:00:B0',  # Huawei Technologies Co.,Ltd
                     '94:04:9C',  # Huawei Technologies Co.,Ltd
                     '94:08:C7',  # Huawei Device Co., Ltd.
                     '94:0B:19',  # Huawei Technologies Co.,Ltd
                     '94:0E:6B',  # Huawei Technologies Co.,Ltd
                     '94:0E:E7',  # Huawei Technologies Co.,Ltd
                     '94:15:B2',  # Huawei Device Co., Ltd.
                     '94:25:33',  # Huawei Technologies Co.,Ltd
                     '94:37:F7',  # Huawei Device Co., Ltd.
                     '94:47:88',  # Huawei Technologies Co.,Ltd
                     '94:60:10',  # Huawei Device Co., Ltd.
                     '94:77:2B',  # Huawei Technologies Co.,Ltd
                     '94:7D:77',  # Huawei Technologies Co.,Ltd
                     '94:90:10',  # Huawei Technologies Co.,Ltd
                     '94:A0:7D',  # Huawei Device Co., Ltd.
                     '94:A4:F9',  # Huawei Technologies Co.,Ltd
                     '94:B2:71',  # Huawei Technologies Co.,Ltd
                     '94:CE:0F',  # Huawei Device Co., Ltd.
                     '94:D0:0D',  # Huawei Technologies Co.,Ltd
                     '94:D2:BC',  # Huawei Technologies Co.,Ltd
                     '94:D5:4D',  # Huawei Technologies Co.,Ltd
                     '94:DB:DA',  # Huawei Technologies Co.,Ltd
                     '94:DF:34',  # Huawei Technologies Co.,Ltd
                     '94:E4:BA',  # Huawei Device Co., Ltd.
                     '94:E7:EA',  # Huawei Technologies Co.,Ltd
                     '94:E9:EE',  # Huawei Device Co., Ltd.
                     '94:FE:22',  # Huawei Technologies Co.,Ltd
                     '98:0D:51',  # Huawei Device Co., Ltd.
                     '98:1A:35',  # Huawei Technologies Co.,Ltd
                     '98:2F:F8',  # Huawei Device Co., Ltd.
                     '98:35:ED',  # Huawei Technologies Co.,Ltd
                     '98:3F:60',  # Huawei Technologies Co.,Ltd
                     '98:44:CE',  # Huawei Technologies Co.,Ltd
                     '98:48:74',  # Huawei Technologies Co.,Ltd
                     '98:4B:06',  # Huawei Technologies Co.,Ltd
                     '98:75:1A',  # Huawei Device Co., Ltd.
                     '98:81:8A',  # Huawei Device Co., Ltd.
                     '98:9C:57',  # Huawei Technologies Co.,Ltd
                     '98:9F:1E',  # Huawei Technologies Co.,Ltd
                     '98:AD:1D',  # Huawei Device Co., Ltd.
                     '98:B3:EF',  # Huawei Device Co., Ltd.
                     '98:D3:D7',  # Huawei Technologies Co.,Ltd
                     '98:E7:F5',  # Huawei Technologies Co.,Ltd
                     '98:F0:83',  # Huawei Technologies Co.,Ltd
                     '9C:1D:36',  # Huawei Technologies Co.,Ltd
                     '9C:28:EF',  # Huawei Technologies Co.,Ltd
                     '9C:37:F4',  # Huawei Technologies Co.,Ltd
                     '9C:52:F8',  # Huawei Technologies Co.,Ltd
                     '9C:56:36',  # Huawei Device Co., Ltd.
                     '9C:69:D1',  # Huawei Technologies Co.,Ltd
                     '9C:71:3A',  # Huawei Technologies Co.,Ltd
                     '9C:73:70',  # Huawei Technologies Co.,Ltd
                     '9C:74:1A',  # Huawei Technologies Co.,Ltd
                     '9C:74:6F',  # Huawei Technologies Co.,Ltd
                     '9C:7D:A3',  # Huawei Technologies Co.,Ltd
                     '9C:82:3F',  # Huawei Device Co., Ltd.
                     '9C:8E:9C',  # Huawei Device Co., Ltd.
                     '9C:95:67',  # Huawei Device Co., Ltd.
                     '9C:9E:71',  # Huawei Device Co., Ltd.
                     '9C:B2:B2',  # Huawei Technologies Co.,Ltd
                     '9C:B2:E8',  # Huawei Technologies Co.,Ltd
                     '9C:BF:CD',  # Huawei Technologies Co.,Ltd
                     '9C:C1:72',  # Huawei Technologies Co.,Ltd
                     '9C:DB:AF',  # Huawei Technologies Co.,Ltd
                     '9C:E3:74',  # Huawei Technologies Co.,Ltd
                     '9C:EC:61',  # Huawei Device Co., Ltd.
                     'A0:08:6F',  # Huawei Technologies Co.,Ltd
                     'A0:1C:8D',  # Huawei Technologies Co.,Ltd
                     'A0:31:DB',  # Huawei Technologies Co.,Ltd
                     'A0:36:79',  # Huawei Technologies Co.,Ltd
                     'A0:40:6F',  # Huawei Technologies Co.,Ltd
                     'A0:41:47',  # Huawei Device Co., Ltd.
                     'A0:42:D1',  # Huawei Device Co., Ltd.
                     'A0:44:5C',  # Huawei Technologies Co.,Ltd
                     'A0:57:E3',  # Huawei Technologies Co.,Ltd
                     'A0:70:B7',  # Huawei Technologies Co.,Ltd
                     'A0:88:9D',  # Huawei Device Co., Ltd.
                     'A0:8C:F8',  # Huawei Technologies Co.,Ltd
                     'A0:8D:16',  # Huawei Technologies Co.,Ltd
                     'A0:A0:DC',  # Huawei Device Co., Ltd.
                     'A0:A3:3B',  # Huawei Technologies Co.,Ltd
                     'A0:AF:12',  # Huawei Technologies Co.,Ltd
                     'A0:C2:0D',  # Huawei Device Co., Ltd.
                     'A0:D7:A0',  # Huawei Device Co., Ltd.
                     'A0:D8:07',  # Huawei Device Co., Ltd.
                     'A0:DE:0F',  # Huawei Device Co., Ltd.
                     'A0:DF:15',  # Huawei Technologies Co.,Ltd
                     'A0:F4:79',  # Huawei Technologies Co.,Ltd
                     'A4:00:E2',  # Huawei Technologies Co.,Ltd
                     'A4:16:E7',  # Huawei Technologies Co.,Ltd
                     'A4:17:8B',  # Huawei Technologies Co.,Ltd
                     'A4:37:3E',  # Huawei Device Co., Ltd.
                     'A4:3B:0E',  # Huawei Device Co., Ltd.
                     'A4:46:B4',  # Huawei Device Co., Ltd.
                     'A4:6C:24',  # Huawei Technologies Co.,Ltd
                     'A4:6D:A4',  # Huawei Technologies Co.,Ltd
                     'A4:71:74',  # Huawei Technologies Co.,Ltd
                     'A4:79:52',  # Huawei Device Co., Ltd.
                     'A4:7B:1A',  # Huawei Device Co., Ltd.
                     'A4:7C:C9',  # Huawei Technologies Co.,Ltd
                     'A4:93:3F',  # Huawei Technologies Co.,Ltd
                     'A4:99:47',  # Huawei Technologies Co.,Ltd
                     'A4:9B:4F',  # Huawei Technologies Co.,Ltd
                     'A4:A4:6B',  # Huawei Technologies Co.,Ltd
                     'A4:AA:FE',  # Huawei Device Co., Ltd.
                     'A4:AC:0F',  # Huawei Device Co., Ltd.
                     'A4:B6:1E',  # Huawei Device Co., Ltd.
                     'A4:BA:76',  # Huawei Technologies Co.,Ltd
                     'A4:BD:C4',  # Huawei Technologies Co.,Ltd
                     'A4:BE:2B',  # Huawei Technologies Co.,Ltd
                     'A4:C5:4E',  # Huawei Device Co., Ltd.
                     'A4:C6:4F',  # Huawei Technologies Co.,Ltd
                     'A4:C7:4B',  # Huawei Device Co., Ltd.
                     'A4:CA:A0',  # Huawei Technologies Co.,Ltd
                     'A4:DC:BE',  # Huawei Technologies Co.,Ltd
                     'A4:DD:58',  # Huawei Technologies Co.,Ltd
                     'A8:0C:63',  # Huawei Technologies Co.,Ltd
                     'A8:2B:CD',  # Huawei Technologies Co.,Ltd
                     'A8:35:12',  # Huawei Device Co., Ltd.
                     'A8:37:59',  # Huawei Device Co., Ltd.
                     'A8:3B:5C',  # Huawei Technologies Co.,Ltd
                     'A8:3E:D3',  # Huawei Technologies Co.,Ltd
                     'A8:49:4D',  # Huawei Technologies Co.,Ltd
                     'A8:50:81',  # Huawei Technologies Co.,Ltd
                     'A8:5A:E0',  # Huawei Device Co., Ltd.
                     'A8:6E:4E',  # Huawei Device Co., Ltd.
                     'A8:7C:45',  # Huawei Technologies Co.,Ltd
                     'A8:7D:12',  # Huawei Technologies Co.,Ltd
                     'A8:89:40',  # Huawei Device Co., Ltd.
                     'A8:AA:7C',  # Huawei Device Co., Ltd.
                     'A8:B2:71',  # Huawei Technologies Co.,Ltd
                     'A8:C0:92',  # Huawei Device Co., Ltd.
                     'A8:C2:52',  # Huawei Device Co., Ltd.
                     'A8:C8:3A',  # Huawei Technologies Co.,Ltd
                     'A8:CA:7B',  # Huawei Technologies Co.,Ltd
                     'A8:D0:81',  # Huawei Device Co., Ltd.
                     'A8:D4:E0',  # Huawei Technologies Co.,Ltd
                     'A8:E5:44',  # Huawei Technologies Co.,Ltd
                     'A8:E9:78',  # Huawei Device Co., Ltd.
                     'A8:F2:66',  # Huawei Device Co., Ltd.
                     'A8:F5:AC',  # Huawei Technologies Co.,Ltd
                     'A8:FF:BA',  # Huawei Technologies Co.,Ltd
                     'AC:07:5F',  # Huawei Technologies Co.,Ltd
                     'AC:31:84',  # Huawei Device Co., Ltd.
                     'AC:33:28',  # Huawei Device Co., Ltd.
                     'AC:47:1B',  # Huawei Device Co., Ltd.
                     'AC:4E:91',  # Huawei Technologies Co.,Ltd
                     'AC:51:AB',  # Huawei Technologies Co.,Ltd
                     'AC:5E:14',  # Huawei Technologies Co.,Ltd
                     'AC:60:89',  # Huawei Technologies Co.,Ltd
                     'AC:61:75',  # Huawei Technologies Co.,Ltd
                     'AC:64:90',  # Huawei Technologies Co.,Ltd
                     'AC:75:1D',  # Huawei Technologies Co.,Ltd
                     'AC:7E:01',  # Huawei Device Co., Ltd.
                     'AC:85:3D',  # Huawei Technologies Co.,Ltd
                     'AC:8D:34',  # Huawei Technologies Co.,Ltd
                     'AC:90:73',  # Huawei Technologies Co.,Ltd
                     'AC:92:32',  # Huawei Technologies Co.,Ltd
                     'AC:93:6A',  # Huawei Device Co., Ltd.
                     'AC:99:29',  # Huawei Technologies Co.,Ltd
                     'AC:B3:B5',  # Huawei Technologies Co.,Ltd
                     'AC:BD:70',  # Huawei Device Co., Ltd.
                     'AC:CF:85',  # Huawei Technologies Co.,Ltd
                     'AC:DC:CA',  # Huawei Technologies Co.,Ltd
                     'AC:E2:15',  # Huawei Technologies Co.,Ltd
                     'AC:E3:42',  # Huawei Technologies Co.,Ltd
                     'AC:E8:7B',  # Huawei Technologies Co.,Ltd
                     'AC:F9:70',  # Huawei Technologies Co.,Ltd
                     'AC:FF:6B',  # Huawei Technologies Co.,Ltd
                     'B0:08:75',  # Huawei Technologies Co.,Ltd
                     'B0:16:56',  # Huawei Technologies Co.,Ltd
                     'B0:21:6F',  # Huawei Technologies Co.,Ltd
                     'B0:24:91',  # Huawei Device Co., Ltd.
                     'B0:2E:E0',  # Huawei Device Co., Ltd.
                     'B0:3A:CE',  # Huawei Device Co., Ltd.
                     'B0:45:02',  # Huawei Device Co., Ltd.
                     'B0:55:08',  # Huawei Technologies Co.,Ltd
                     'B0:5B:67',  # Huawei Technologies Co.,Ltd
                     'B0:73:5D',  # Huawei Device Co., Ltd.
                     'B0:76:1B',  # Huawei Technologies Co.,Ltd
                     'B0:89:00',  # Huawei Technologies Co.,Ltd
                     'B0:98:BC',  # Huawei Device Co., Ltd.
                     'B0:99:5A',  # Huawei Technologies Co.,Ltd
                     'B0:A4:F0',  # Huawei Technologies Co.,Ltd
                     'B0:C7:87',  # Huawei Technologies Co.,Ltd
                     'B0:CA:E7',  # Huawei Device Co., Ltd.
                     'B0:CC:FE',  # Huawei Device Co., Ltd.
                     'B0:E1:7E',  # Huawei Technologies Co.,Ltd
                     'B0:E5:ED',  # Huawei Technologies Co.,Ltd
                     'B0:EB:57',  # Huawei Technologies Co.,Ltd
                     'B0:EC:DD',  # Huawei Technologies Co.,Ltd
                     'B0:FA:8B',  # Huawei Device Co., Ltd.
                     'B0:FE:E5',  # Huawei Device Co., Ltd.
                     'B4:09:31',  # Huawei Technologies Co.,Ltd
                     'B4:14:E6',  # Huawei Technologies Co.,Ltd
                     'B4:15:13',  # Huawei Technologies Co.,Ltd
                     'B4:30:52',  # Huawei Technologies Co.,Ltd
                     'B4:3A:E2',  # Huawei Technologies Co.,Ltd
                     'B4:43:26',  # Huawei Technologies Co.,Ltd
                     'B4:61:42',  # Huawei Technologies Co.,Ltd
                     'B4:6E:08',  # Huawei Technologies Co.,Ltd
                     'B4:86:55',  # Huawei Technologies Co.,Ltd
                     'B4:89:01',  # Huawei Technologies Co.,Ltd
                     'B4:A8:98',  # Huawei Device Co., Ltd.
                     'B4:B0:55',  # Huawei Technologies Co.,Ltd
                     'B4:C2:F7',  # Huawei Device Co., Ltd.
                     'B4:CD:27',  # Huawei Technologies Co.,Ltd
                     'B4:F1:8C',  # Huawei Device Co., Ltd.
                     'B4:F5:8E',  # Huawei Technologies Co.,Ltd
                     'B4:FB:F9',  # Huawei Technologies Co.,Ltd
                     'B4:FF:98',  # Huawei Technologies Co.,Ltd
                     'B8:08:D7',  # Huawei Technologies Co.,Ltd
                     'B8:14:5C',  # Huawei Device Co., Ltd.
                     'B8:27:C5',  # Huawei Device Co., Ltd.
                     'B8:2B:68',  # Huawei Device Co., Ltd.
                     'B8:56:00',  # Huawei Technologies Co.,Ltd
                     'B8:5D:C3',  # Huawei Technologies Co.,Ltd
                     'B8:5F:B0',  # Huawei Technologies Co.,Ltd
                     'B8:7C:D0',  # Huawei Device Co., Ltd.
                     'B8:7E:40',  # Huawei Device Co., Ltd.
                     'B8:85:7B',  # Huawei Technologies Co.,Ltd
                     'B8:8E:82',  # Huawei Device Co., Ltd.
                     'B8:94:36',  # Huawei Technologies Co.,Ltd
                     'B8:9F:CC',  # Huawei Technologies Co.,Ltd
                     'B8:BC:1B',  # Huawei Technologies Co.,Ltd
                     'B8:C3:85',  # Huawei Technologies Co.,Ltd
                     'B8:D6:F6',  # Huawei Technologies Co.,Ltd
                     'B8:DA:E8',  # Huawei Device Co., Ltd.
                     'B8:E3:B1',  # Huawei Technologies Co.,Ltd
                     'BC:18:96',  # Huawei Technologies Co.,Ltd
                     'BC:1A:E4',  # Huawei Device Co., Ltd.
                     'BC:1E:85',  # Huawei Technologies Co.,Ltd
                     'BC:25:E0',  # Huawei Technologies Co.,Ltd
                     'BC:2E:F6',  # Huawei Device Co., Ltd.
                     'BC:3D:85',  # Huawei Technologies Co.,Ltd
                     'BC:3F:8F',  # Huawei Technologies Co.,Ltd
                     'BC:4C:78',  # Huawei Technologies Co.,Ltd
                     'BC:4C:A0',  # Huawei Technologies Co.,Ltd
                     'BC:62:0E',  # Huawei Technologies Co.,Ltd
                     'BC:75:74',  # Huawei Technologies Co.,Ltd
                     'BC:76:70',  # Huawei Technologies Co.,Ltd
                     'BC:76:C5',  # Huawei Technologies Co.,Ltd
                     'BC:7B:72',  # Huawei Device Co., Ltd.
                     'BC:7F:7B',  # Huawei Device Co., Ltd.
                     'BC:97:89',  # Huawei Device Co., Ltd.
                     'BC:99:30',  # Huawei Technologies Co.,Ltd
                     'BC:9A:53',  # Huawei Device Co., Ltd.
                     'BC:9C:31',  # Huawei Technologies Co.,Ltd
                     'BC:B0:E7',  # Huawei Technologies Co.,Ltd
                     'BC:C4:27',  # Huawei Technologies Co.,Ltd
                     'BC:D2:06',  # Huawei Technologies Co.,Ltd
                     'BC:E2:65',  # Huawei Technologies Co.,Ltd
                     'C0:06:0C',  # Huawei Technologies Co.,Ltd
                     'C0:3E:50',  # Huawei Technologies Co.,Ltd
                     'C0:3F:DD',  # Huawei Technologies Co.,Ltd
                     'C0:4E:8A',  # Huawei Technologies Co.,Ltd
                     'C0:70:09',  # Huawei Technologies Co.,Ltd
                     'C0:78:31',  # Huawei Device Co., Ltd.
                     'C0:83:C9',  # Huawei Device Co., Ltd.
                     'C0:84:E0',  # Huawei Technologies Co.,Ltd
                     'C0:8B:05',  # Huawei Technologies Co.,Ltd
                     'C0:A9:38',  # Huawei Technologies Co.,Ltd
                     'C0:B4:7D',  # Huawei Device Co., Ltd.
                     'C0:B5:CD',  # Huawei Device Co., Ltd.
                     'C0:BC:9A',  # Huawei Technologies Co.,Ltd
                     'C0:BF:AC',  # Huawei Device Co., Ltd.
                     'C0:BF:C0',  # Huawei Technologies Co.,Ltd
                     'C0:D0:26',  # Huawei Device Co., Ltd.
                     'C0:D1:93',  # Huawei Device Co., Ltd.
                     'C0:D4:6B',  # Huawei Device Co., Ltd.
                     'C0:DC:D7',  # Huawei Device Co., Ltd.
                     'C0:E0:18',  # Huawei Technologies Co.,Ltd
                     'C0:E1:BE',  # Huawei Technologies Co.,Ltd
                     'C0:E3:FB',  # Huawei Technologies Co.,Ltd
                     'C0:F4:E6',  # Huawei Technologies Co.,Ltd
                     'C0:F6:C2',  # Huawei Technologies Co.,Ltd
                     'C0:F6:EC',  # Huawei Technologies Co.,Ltd
                     'C0:F9:B0',  # Huawei Technologies Co.,Ltd
                     'C0:FF:A8',  # Huawei Technologies Co.,Ltd
                     'C4:05:28',  # Huawei Technologies Co.,Ltd
                     'C4:06:83',  # Huawei Technologies Co.,Ltd
                     'C4:07:2F',  # Huawei Technologies Co.,Ltd
                     'C4:0D:96',  # Huawei Technologies Co.,Ltd
                     'C4:12:EC',  # Huawei Technologies Co.,Ltd
                     'C4:16:88',  # Huawei Device Co., Ltd.
                     'C4:16:C8',  # Huawei Technologies Co.,Ltd
                     'C4:17:0E',  # Huawei Device Co., Ltd.
                     'C4:27:8C',  # Huawei Device Co., Ltd.
                     'C4:2B:44',  # Huawei Device Co., Ltd.
                     'C4:34:5B',  # Huawei Technologies Co.,Ltd
                     'C4:44:7D',  # Huawei Technologies Co.,Ltd
                     'C4:47:3F',  # Huawei Technologies Co.,Ltd
                     'C4:4F:5F',  # Huawei Device Co., Ltd.
                     'C4:5A:86',  # Huawei Device Co., Ltd.
                     'C4:5E:5C',  # Huawei Technologies Co.,Ltd
                     'C4:67:D1',  # Huawei Technologies Co.,Ltd
                     'C4:69:F0',  # Huawei Technologies Co.,Ltd
                     'C4:75:EA',  # Huawei Technologies Co.,Ltd
                     'C4:78:A2',  # Huawei Device Co., Ltd.
                     'C4:80:25',  # Huawei Device Co., Ltd.
                     'C4:86:E9',  # Huawei Technologies Co.,Ltd
                     'C4:9D:08',  # Huawei Device Co., Ltd.
                     'C4:9F:4C',  # Huawei Technologies Co.,Ltd
                     'C4:A1:AE',  # Huawei Device Co., Ltd.
                     'C4:A4:02',  # Huawei Technologies Co.,Ltd
                     'C4:AA:99',  # Huawei Technologies Co.,Ltd
                     'C4:B8:B4',  # Huawei Technologies Co.,Ltd
                     'C4:D4:38',  # Huawei Technologies Co.,Ltd
                     'C4:D7:38',  # Huawei Device Co., Ltd.
                     'C4:DB:04',  # Huawei Technologies Co.,Ltd
                     'C4:DE:7B',  # Huawei Device Co., Ltd.
                     'C4:E2:87',  # Huawei Technologies Co.,Ltd
                     'C4:F0:81',  # Huawei Technologies Co.,Ltd
                     'C4:FB:AA',  # Huawei Technologies Co.,Ltd
                     'C4:FF:1F',  # Huawei Technologies Co.,Ltd
                     'C4:FF:22',  # Huawei Device Co., Ltd.
                     'C8:0C:C8',  # Huawei Technologies Co.,Ltd
                     'C8:14:51',  # Huawei Technologies Co.,Ltd
                     'C8:1F:BE',  # Huawei Technologies Co.,Ltd
                     'C8:33:E5',  # Huawei Technologies Co.,Ltd
                     'C8:39:AC',  # Huawei Device Co., Ltd.
                     'C8:3E:9E',  # Huawei Device Co., Ltd.
                     'C8:50:CE',  # Huawei Technologies Co.,Ltd
                     'C8:51:95',  # Huawei Technologies Co.,Ltd
                     'C8:68:DE',  # Huawei Device Co., Ltd.
                     'C8:84:CF',  # Huawei Technologies Co.,Ltd
                     'C8:8D:83',  # Huawei Technologies Co.,Ltd
                     'C8:94:BB',  # Huawei Technologies Co.,Ltd
                     'C8:9D:18',  # Huawei Device Co., Ltd.
                     'C8:9F:1A',  # Huawei Technologies Co.,Ltd
                     'C8:A7:76',  # Huawei Technologies Co.,Ltd
                     'C8:B6:D3',  # Huawei Technologies Co.,Ltd
                     'C8:BB:81',  # Huawei Device Co., Ltd.
                     'C8:BC:9C',  # Huawei Device Co., Ltd.
                     'C8:BF:FE',  # Huawei Device Co., Ltd.
                     'C8:C2:FA',  # Huawei Technologies Co.,Ltd
                     'C8:C4:65',  # Huawei Technologies Co.,Ltd
                     'C8:CA:63',  # Huawei Device Co., Ltd.
                     'C8:D1:5E',  # Huawei Technologies Co.,Ltd
                     'C8:E6:00',  # Huawei Technologies Co.,Ltd
                     'CC:05:77',  # Huawei Technologies Co.,Ltd
                     'CC:08:7B',  # Huawei Technologies Co.,Ltd
                     'CC:1E:56',  # Huawei Technologies Co.,Ltd
                     'CC:1E:97',  # Huawei Technologies Co.,Ltd
                     'CC:20:8C',  # Huawei Technologies Co.,Ltd
                     'CC:32:96',  # Huawei Device Co., Ltd.
                     'CC:3D:D1',  # Huawei Technologies Co.,Ltd
                     'CC:53:B5',  # Huawei Technologies Co.,Ltd
                     'CC:5C:61',  # Huawei Device Co., Ltd.
                     'CC:64:A6',  # Huawei Technologies Co.,Ltd
                     'CC:89:5E',  # Huawei Technologies Co.,Ltd
                     'CC:96:A0',  # Huawei Technologies Co.,Ltd
                     'CC:A2:23',  # Huawei Technologies Co.,Ltd
                     'CC:B0:A8',  # Huawei Device Co., Ltd.
                     'CC:B1:82',  # Huawei Technologies Co.,Ltd
                     'CC:B7:C4',  # Huawei Technologies Co.,Ltd
                     'CC:BA:6F',  # Huawei Technologies Co.,Ltd
                     'CC:BB:FE',  # Huawei Technologies Co.,Ltd
                     'CC:BC:2B',  # Huawei Device Co., Ltd.
                     'CC:BC:E3',  # Huawei Technologies Co.,Ltd
                     'CC:CC:81',  # Huawei Technologies Co.,Ltd
                     'CC:D7:3C',  # Huawei Technologies Co.,Ltd
                     'CC:FA:66',  # Huawei Device Co., Ltd.
                     'CC:FF:90',  # Huawei Device Co., Ltd.
                     'D0:05:E4',  # Huawei Device Co., Ltd.
                     'D0:0D:F7',  # Huawei Device Co., Ltd.
                     'D0:16:B4',  # Huawei Technologies Co.,Ltd
                     'D0:2D:B3',  # Huawei Technologies Co.,Ltd
                     'D0:3E:5C',  # Huawei Technologies Co.,Ltd
                     'D0:4E:99',  # Huawei Technologies Co.,Ltd
                     'D0:61:58',  # Huawei Technologies Co.,Ltd
                     'D0:65:CA',  # Huawei Technologies Co.,Ltd
                     'D0:6F:82',  # Huawei Technologies Co.,Ltd
                     'D0:7A:B5',  # Huawei Technologies Co.,Ltd
                     'D0:7D:33',  # Huawei Device Co., Ltd.
                     'D0:7E:01',  # Huawei Device Co., Ltd.
                     'D0:94:CF',  # Huawei Technologies Co.,Ltd
                     'D0:B4:5D',  # Huawei Device Co., Ltd.
                     'D0:C6:5B',  # Huawei Technologies Co.,Ltd
                     'D0:D0:4B',  # Huawei Technologies Co.,Ltd
                     'D0:D7:83',  # Huawei Technologies Co.,Ltd
                     'D0:D7:BE',  # Huawei Technologies Co.,Ltd
                     'D0:EF:C1',  # Huawei Technologies Co.,Ltd
                     'D0:F3:F5',  # Huawei Device Co., Ltd.
                     'D0:F4:F7',  # Huawei Device Co., Ltd.
                     'D0:FF:98',  # Huawei Technologies Co.,Ltd
                     'D4:40:F0',  # Huawei Technologies Co.,Ltd
                     'D4:46:49',  # Huawei Technologies Co.,Ltd
                     'D4:4F:67',  # Huawei Technologies Co.,Ltd
                     'D4:5F:7A',  # Huawei Technologies Co.,Ltd
                     'D4:61:2E',  # Huawei Technologies Co.,Ltd
                     'D4:62:EA',  # Huawei Technologies Co.,Ltd
                     'D4:6A:A8',  # Huawei Technologies Co.,Ltd
                     'D4:6B:A6',  # Huawei Technologies Co.,Ltd
                     'D4:6E:5C',  # Huawei Technologies Co.,Ltd
                     'D4:74:15',  # Huawei Device Co., Ltd.
                     'D4:79:54',  # Huawei Device Co., Ltd.
                     'D4:88:66',  # Huawei Technologies Co.,Ltd
                     'D4:8F:A2',  # Huawei Device Co., Ltd.
                     'D4:94:00',  # Huawei Technologies Co.,Ltd
                     'D4:94:E8',  # Huawei Technologies Co.,Ltd
                     'D4:9F:DD',  # Huawei Device Co., Ltd.
                     'D4:A1:48',  # Huawei Technologies Co.,Ltd
                     'D4:A9:23',  # Huawei Technologies Co.,Ltd
                     'D4:B1:10',  # Huawei Technologies Co.,Ltd
                     'D4:BB:E6',  # Huawei Device Co., Ltd.
                     'D4:D5:1B',  # Huawei Technologies Co.,Ltd
                     'D4:D8:92',  # Huawei Technologies Co.,Ltd
                     'D4:F2:42',  # Huawei Device Co., Ltd.
                     'D4:F9:A1',  # Huawei Technologies Co.,Ltd
                     'D8:0A:60',  # Huawei Technologies Co.,Ltd
                     'D8:10:9F',  # Huawei Technologies Co.,Ltd
                     'D8:1B:B5',  # Huawei Technologies Co.,Ltd
                     'D8:29:18',  # Huawei Technologies Co.,Ltd
                     'D8:29:F8',  # Huawei Technologies Co.,Ltd
                     'D8:40:08',  # Huawei Technologies Co.,Ltd
                     'D8:47:BB',  # Huawei Device Co., Ltd.
                     'D8:49:0B',  # Huawei Technologies Co.,Ltd
                     'D8:59:82',  # Huawei Technologies Co.,Ltd
                     'D8:67:D3',  # Huawei Device Co., Ltd.
                     'D8:68:52',  # Huawei Technologies Co.,Ltd
                     'D8:6D:17',  # Huawei Technologies Co.,Ltd
                     'D8:76:AE',  # Huawei Technologies Co.,Ltd
                     'D8:80:DC',  # Huawei Device Co., Ltd.
                     'D8:88:63',  # Huawei Technologies Co.,Ltd
                     'D8:8A:DC',  # Huawei Device Co., Ltd.
                     'D8:9B:3B',  # Huawei Technologies Co.,Ltd
                     'D8:9E:61',  # Huawei Device Co., Ltd.
                     'D8:A4:91',  # Huawei Device Co., Ltd.
                     'D8:B2:49',  # Huawei Device Co., Ltd.
                     'D8:C7:71',  # Huawei Technologies Co.,Ltd
                     'D8:CC:98',  # Huawei Device Co., Ltd.
                     'D8:DA:F1',  # Huawei Technologies Co.,Ltd
                     'D8:EF:42',  # Huawei Device Co., Ltd.
                     'DC:09:4C',  # Huawei Technologies Co.,Ltd
                     'DC:16:B2',  # Huawei Technologies Co.,Ltd
                     'DC:21:E2',  # Huawei Technologies Co.,Ltd
                     'DC:27:27',  # Huawei Device Co., Ltd.
                     'DC:2D:3C',  # Huawei Device Co., Ltd.
                     'DC:33:3D',  # Huawei Device Co., Ltd.
                     'DC:62:1F',  # Huawei Technologies Co.,Ltd
                     'DC:6B:1B',  # Huawei Device Co., Ltd.
                     'DC:72:9B',  # Huawei Technologies Co.,Ltd
                     'DC:73:85',  # Huawei Device Co., Ltd.
                     'DC:77:94',  # Huawei Device Co., Ltd.
                     'DC:90:88',  # Huawei Technologies Co.,Ltd
                     'DC:91:66',  # Huawei Device Co., Ltd.
                     'DC:99:14',  # Huawei Technologies Co.,Ltd
                     'DC:A7:82',  # Huawei Technologies Co.,Ltd
                     'DC:C6:4B',  # Huawei Technologies Co.,Ltd
                     'DC:D2:FC',  # Huawei Technologies Co.,Ltd
                     'DC:D2:FD',  # Huawei Technologies Co.,Ltd
                     'DC:D4:44',  # Huawei Device Co., Ltd.
                     'DC:D7:A0',  # Huawei Device Co., Ltd.
                     'DC:D9:16',  # Huawei Technologies Co.,Ltd
                     'DC:DB:27',  # Huawei Device Co., Ltd.
                     'DC:EE:06',  # Huawei Technologies Co.,Ltd
                     'DC:EF:80',  # Huawei Technologies Co.,Ltd
                     'E0:00:84',  # Huawei Technologies Co.,Ltd
                     'E0:06:30',  # Huawei Technologies Co.,Ltd
                     'E0:0C:E5',  # Huawei Technologies Co.,Ltd
                     'E0:19:1D',  # Huawei Technologies Co.,Ltd
                     'E0:1F:6A',  # Huawei Device Co., Ltd.
                     'E0:24:7F',  # Huawei Technologies Co.,Ltd
                     'E0:24:81',  # Huawei Technologies Co.,Ltd
                     'E0:28:61',  # Huawei Technologies Co.,Ltd
                     'E0:2E:3F',  # Huawei Device Co., Ltd.
                     'E0:36:76',  # Huawei Technologies Co.,Ltd
                     'E0:40:07',  # Huawei Device Co., Ltd.
                     'E0:4B:A6',  # Huawei Technologies Co.,Ltd
                     'E0:6C:C5',  # Huawei Device Co., Ltd.
                     'E0:77:26',  # Huawei Device Co., Ltd.
                     'E0:97:96',  # Huawei Technologies Co.,Ltd
                     'E0:A3:AC',  # Huawei Technologies Co.,Ltd
                     'E0:AE:A2',  # Huawei Technologies Co.,Ltd
                     'E0:CC:7A',  # Huawei Technologies Co.,Ltd
                     'E0:D4:62',  # Huawei Device Co., Ltd.
                     'E0:DA:90',  # Huawei Technologies Co.,Ltd
                     'E0:E0:FC',  # Huawei Device Co., Ltd.
                     'E0:E3:7C',  # Huawei Device Co., Ltd.
                     'E0:F4:42',  # Huawei Device Co., Ltd.
                     'E4:07:2B',  # Huawei Device Co., Ltd.
                     'E4:0A:16',  # Huawei Technologies Co.,Ltd
                     'E4:0E:EE',  # Huawei Technologies Co.,Ltd
                     'E4:19:C1',  # Huawei Technologies Co.,Ltd
                     'E4:26:8B',  # Huawei Device Co., Ltd.
                     'E4:34:93',  # Huawei Technologies Co.,Ltd
                     'E4:35:C8',  # Huawei Technologies Co.,Ltd
                     'E4:3E:C6',  # Huawei Technologies Co.,Ltd
                     'E4:68:A3',  # Huawei Technologies Co.,Ltd
                     'E4:72:E2',  # Huawei Technologies Co.,Ltd
                     'E4:77:27',  # Huawei Technologies Co.,Ltd
                     'E4:7E:66',  # Huawei Technologies Co.,Ltd
                     'E4:82:10',  # Huawei Technologies Co.,Ltd
                     'E4:83:26',  # Huawei Technologies Co.,Ltd
                     'E4:8F:1D',  # Huawei Device Co., Ltd.
                     'E4:90:2A',  # Huawei Technologies Co.,Ltd
                     'E4:A7:C5',  # Huawei Technologies Co.,Ltd
                     'E4:A8:B6',  # Huawei Technologies Co.,Ltd
                     'E4:B2:24',  # Huawei Technologies Co.,Ltd
                     'E4:B5:55',  # Huawei Device Co., Ltd.
                     'E4:BE:FB',  # Huawei Technologies Co.,Ltd
                     'E4:C2:D1',  # Huawei Technologies Co.,Ltd
                     'E4:D3:73',  # Huawei Technologies Co.,Ltd
                     'E4:DC:43',  # Huawei Device Co., Ltd.
                     'E4:DC:CC',  # Huawei Technologies Co.,Ltd
                     'E4:FB:5D',  # Huawei Technologies Co.,Ltd
                     'E4:FD:A1',  # Huawei Technologies Co.,Ltd
                     'E8:08:8B',  # Huawei Technologies Co.,Ltd
                     'E8:13:6E',  # Huawei Technologies Co.,Ltd
                     'E8:1E:92',  # Huawei Device Co., Ltd.
                     'E8:28:8D',  # Huawei Device Co., Ltd.
                     'E8:2B:C5',  # Huawei Device Co., Ltd.
                     'E8:3F:67',  # Huawei Device Co., Ltd.
                     'E8:4D:74',  # Huawei Technologies Co.,Ltd
                     'E8:4D:D0',  # Huawei Technologies Co.,Ltd
                     'E8:4F:A7',  # Huawei Device Co., Ltd.
                     'E8:68:19',  # Huawei Technologies Co.,Ltd
                     'E8:6D:E9',  # Huawei Technologies Co.,Ltd
                     'E8:84:C6',  # Huawei Technologies Co.,Ltd
                     'E8:A3:4E',  # Huawei Technologies Co.,Ltd
                     'E8:A6:60',  # Huawei Technologies Co.,Ltd
                     'E8:A6:CA',  # Huawei Device Co., Ltd.
                     'E8:AB:F3',  # Huawei Technologies Co.,Ltd
                     'E8:AC:23',  # Huawei Technologies Co.,Ltd
                     'E8:BD:D1',  # Huawei Technologies Co.,Ltd
                     'E8:CD:2D',  # Huawei Technologies Co.,Ltd
                     'E8:D7:65',  # Huawei Technologies Co.,Ltd
                     'E8:D7:75',  # Huawei Technologies Co.,Ltd
                     'E8:EA:4D',  # Huawei Technologies Co.,Ltd
                     'E8:F6:54',  # Huawei Technologies Co.,Ltd
                     'E8:F7:2F',  # Huawei Technologies Co.,Ltd
                     'E8:F9:D4',  # Huawei Technologies Co.,Ltd
                     'E8:FA:23',  # Huawei Device Co., Ltd.
                     'E8:FD:35',  # Huawei Device Co., Ltd.
                     'E8:FF:98',  # Huawei Device Co., Ltd.
                     'EC:1A:02',  # Huawei Technologies Co.,Ltd
                     'EC:23:3D',  # Huawei Technologies Co.,Ltd
                     'EC:38:8F',  # Huawei Technologies Co.,Ltd
                     'EC:3A:52',  # Huawei Device Co., Ltd.
                     'EC:3C:BB',  # Huawei Device Co., Ltd.
                     'EC:4D:47',  # Huawei Technologies Co.,Ltd
                     'EC:55:1C',  # Huawei Technologies Co.,Ltd
                     'EC:56:23',  # Huawei Technologies Co.,Ltd
                     'EC:75:3E',  # Huawei Technologies Co.,Ltd
                     'EC:7C:2C',  # Huawei Technologies Co.,Ltd
                     'EC:81:9C',  # Huawei Technologies Co.,Ltd
                     'EC:89:14',  # Huawei Technologies Co.,Ltd
                     'EC:8C:9A',  # Huawei Technologies Co.,Ltd
                     'EC:A1:D1',  # Huawei Technologies Co.,Ltd
                     'EC:A6:2F',  # Huawei Technologies Co.,Ltd
                     'EC:AA:8F',  # Huawei Technologies Co.,Ltd
                     'EC:C0:1B',  # Huawei Technologies Co.,Ltd
                     'EC:C5:D2',  # Huawei Device Co., Ltd.
                     'EC:CB:30',  # Huawei Technologies Co.,Ltd
                     'EC:E6:1D',  # Huawei Device Co., Ltd.
                     'EC:F8:D0',  # Huawei Technologies Co.,Ltd
                     'F0:0F:EC',  # Huawei Technologies Co.,Ltd
                     'F0:25:8E',  # Huawei Technologies Co.,Ltd
                     'F0:2F:A7',  # Huawei Technologies Co.,Ltd
                     'F0:33:E5',  # Huawei Technologies Co.,Ltd
                     'F0:37:CF',  # Huawei Device Co., Ltd.
                     'F0:3F:95',  # Huawei Technologies Co.,Ltd
                     'F0:42:F5',  # Huawei Device Co., Ltd.
                     'F0:43:47',  # Huawei Technologies Co.,Ltd
                     'F0:55:01',  # Huawei Device Co., Ltd.
                     'F0:63:F9',  # Huawei Technologies Co.,Ltd
                     'F0:98:38',  # Huawei Technologies Co.,Ltd
                     'F0:9B:B8',  # Huawei Technologies Co.,Ltd
                     'F0:A0:B1',  # Huawei Technologies Co.,Ltd
                     'F0:A9:51',  # Huawei Technologies Co.,Ltd
                     'F0:B1:3F',  # Huawei Device Co., Ltd.
                     'F0:C4:2F',  # Huawei Device Co., Ltd.
                     'F0:C4:78',  # Huawei Technologies Co.,Ltd
                     'F0:C8:50',  # Huawei Technologies Co.,Ltd
                     'F0:C8:B5',  # Huawei Technologies Co.,Ltd
                     'F0:E4:A2',  # Huawei Technologies Co.,Ltd
                     'F0:F7:E7',  # Huawei Technologies Co.,Ltd
                     'F0:F7:FC',  # Huawei Technologies Co.,Ltd
                     'F0:FA:C7',  # Huawei Device Co., Ltd.
                     'F0:FE:E7',  # Huawei Device Co., Ltd.
                     'F4:1D:6B',  # Huawei Technologies Co.,Ltd
                     'F4:38:C1',  # Huawei Device Co., Ltd.
                     'F4:41:9E',  # Huawei Device Co., Ltd.
                     'F4:45:88',  # Huawei Technologies Co.,Ltd
                     'F4:4C:7F',  # Huawei Technologies Co.,Ltd
                     'F4:55:9C',  # Huawei Technologies Co.,Ltd
                     'F4:62:DC',  # Huawei Device Co., Ltd.
                     'F4:63:1F',  # Huawei Technologies Co.,Ltd
                     'F4:79:46',  # Huawei Technologies Co.,Ltd
                     'F4:79:60',  # Huawei Technologies Co.,Ltd
                     'F4:87:C5',  # Huawei Device Co., Ltd.
                     'F4:8E:92',  # Huawei Technologies Co.,Ltd
                     'F4:9F:F3',  # Huawei Technologies Co.,Ltd
                     'F4:A4:D6',  # Huawei Technologies Co.,Ltd
                     'F4:A5:9D',  # Huawei Device Co., Ltd.
                     'F4:B7:8D',  # Huawei Technologies Co.,Ltd
                     'F4:BF:80',  # Huawei Technologies Co.,Ltd
                     'F4:C7:14',  # Huawei Technologies Co.,Ltd
                     'F4:CB:52',  # Huawei Technologies Co.,Ltd
                     'F4:DC:F9',  # Huawei Technologies Co.,Ltd
                     'F4:DE:AF',  # Huawei Technologies Co.,Ltd
                     'F4:E3:FB',  # Huawei Technologies Co.,Ltd
                     'F4:E4:51',  # Huawei Technologies Co.,Ltd
                     'F4:E5:F2',  # Huawei Technologies Co.,Ltd
                     'F4:FB:B8',  # Huawei Technologies Co.,Ltd
                     'F8:00:A1',  # Huawei Technologies Co.,Ltd
                     'F8:01:13',  # Huawei Technologies Co.,Ltd
                     'F8:07:5D',  # Huawei Device Co., Ltd.
                     'F8:20:A9',  # Huawei Device Co., Ltd.
                     'F8:23:B2',  # Huawei Technologies Co.,Ltd
                     'F8:28:C9',  # Huawei Technologies Co.,Ltd
                     'F8:2B:7F',  # Huawei Device Co., Ltd.
                     'F8:2E:3F',  # Huawei Technologies Co.,Ltd
                     'F8:2F:65',  # Huawei Device Co., Ltd.
                     'F8:3B:7E',  # Huawei Device Co., Ltd.
                     'F8:3D:FF',  # Huawei Technologies Co.,Ltd
                     'F8:3E:95',  # Huawei Technologies Co.,Ltd
                     'F8:4A:BF',  # Huawei Technologies Co.,Ltd
                     'F8:4C:DA',  # Huawei Technologies Co.,Ltd
                     'F8:53:29',  # Huawei Technologies Co.,Ltd
                     'F8:6E:EE',  # Huawei Technologies Co.,Ltd
                     'F8:75:88',  # Huawei Technologies Co.,Ltd
                     'F8:79:07',  # Huawei Device Co., Ltd.
                     'F8:7D:3F',  # Huawei Device Co., Ltd.
                     'F8:95:22',  # Huawei Technologies Co.,Ltd
                     'F8:97:53',  # Huawei Device Co., Ltd.
                     'F8:98:B9',  # Huawei Technologies Co.,Ltd
                     'F8:98:EF',  # Huawei Technologies Co.,Ltd
                     'F8:9A:25',  # Huawei Technologies Co.,Ltd
                     'F8:9A:78',  # Huawei Technologies Co.,Ltd
                     'F8:AF:05',  # Huawei Device Co., Ltd.
                     'F8:B1:32',  # Huawei Technologies Co.,Ltd
                     'F8:BF:09',  # Huawei Technologies Co.,Ltd
                     'F8:C3:9E',  # Huawei Technologies Co.,Ltd
                     'F8:DE:73',  # Huawei Technologies Co.,Ltd
                     'F8:E8:11',  # Huawei Technologies Co.,Ltd
                     'F8:F7:B9',  # Huawei Technologies Co.,Ltd
                     'FC:07:36',  # Huawei Device Co., Ltd.
                     'FC:11:93',  # Huawei Technologies Co.,Ltd
                     'FC:12:2C',  # Huawei Technologies Co.,Ltd
                     'FC:18:03',  # Huawei Technologies Co.,Ltd
                     'FC:1B:D1',  # Huawei Technologies Co.,Ltd
                     'FC:1D:3A',  # Huawei Technologies Co.,Ltd
                     'FC:3F:7C',  # Huawei Technologies Co.,Ltd
                     'FC:48:EF',  # Huawei Technologies Co.,Ltd
                     'FC:4D:A6',  # Huawei Technologies Co.,Ltd
                     'FC:51:B5',  # Huawei Technologies Co.,Ltd
                     'FC:65:B3',  # Huawei Device Co., Ltd.
                     'FC:73:FB',  # Huawei Technologies Co.,Ltd
                     'FC:86:2A',  # Huawei Device Co., Ltd.
                     'FC:87:43',  # Huawei Technologies Co.,Ltd
                     'FC:94:35',  # Huawei Technologies Co.,Ltd
                     'FC:A0:F3',  # Huawei Technologies Co.,Ltd
                     'FC:AB:90',  # Huawei Technologies Co.,Ltd
                     'FC:BC:D1',  # Huawei Technologies Co.,Ltd
                     'FC:E3:3C',  # Huawei Technologies Co.,Ltd
                     'FC:F7:7B'  # Huawei Device Co., Ltd.
                     ]

# Hytera MAC prefix
hytera_mac_prefix = ['64:69:BC', '9C:06:6E']

# Hangzhou Hikvision Digital MAC prefix
hangzhou_mac_prefix = ['00:0E:A3',  # CNCR-IT CO.,LTD,HangZhou P.R.CHINA
                       '00:0F:E2',  # Hangzhou H3C Technologies Co., Limited
                       '00:11:D5',  # Hangzhou Sunyard System Engineering Co.,Ltd.
                       '00:1B:C5:0A:10',  # Hangzhou Zhiping Technology Co., Ltd.
                       '00:1C:47',  # Hangzhou Hollysys Automation Co., Ltd
                       '00:1D:A4',  # Hangzhou System Technology CO., LTD
                       '00:1D:DC',  # Hangzhou DeChangLong Tech&Info Co.,Ltd
                       '00:22:AC',  # Hangzhou Siyuan Tech. Co., Ltd
                       '00:23:89',  # Hangzhou H3C Technologies Co., Limited
                       '00:24:AC',  # Hangzhou DPtech Technologies Co., Ltd.
                       '00:69:67:90',  # Hangzhou Wise IOT Technology Co.,Ltd
                       '00:B8:10',  # Yichip Microelectronics (Hangzhou) Co.,Ltd
                       '04:03:12',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '08:54:11',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '08:A1:89',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '08:BC:20',  # Hangzhou Royal Cloud Technology Co., Ltd
                       '08:CC:81',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '08:F8:0D:70',  # Hangzhou YILI Communication Equipment Ltd
                       '0C:75:D2',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '0C:DA:41',  # Hangzhou H3C Technologies Co., Limited
                       '10:12:FB',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '18:45:B3:B0',  # Hangzhou CCRFID Microelectronic Co., Ltd.
                       '18:68:CB',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '18:74:E2:50',  # Hangzhou Zhouju Electronic Technological Co.,Ltd
                       '18:80:25',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '18:C3:F4:C0',  # Hangzhou Zhongkejiguang Technology Co., Ltd
                       '1C:87:79:A0',  # Hangzhou Xiaowen Intelligent Technology Co., Ltd.
                       '1C:C0:E1:10',  # Hangzhou Kaierda Electric Welding Machine Co.,Ltd
                       '1C:C0:E1:30',  # Hangzhou Softel Optic Co., Ltd
                       '1C:C1:BC',  # Yichip Microelectronics (Hangzhou) Co.,Ltd
                       '20:02:FE',  # Hangzhou Dangbei Network Technology Co., Ltd
                       '20:0A:0D:E0',  # Hangzhou DANGBEI NETWORK TECH.Co.,Ltd
                       '20:96:8A',  # China Mobile (Hangzhou) Information Technology Co., Ltd.
                       '20:BB:BC',  # Hangzhou Ezviz Software Co.,Ltd.
                       '24:00:FA',  # China Mobile (Hangzhou) Information Technology Co., Ltd
                       '24:0F:9B',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '24:1B:44',  # Hangzhou Tuners Electronics Co., Ltd
                       '24:28:FD',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '24:32:AE',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '24:48:45',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '24:DF:A7',  # Hangzhou BroadLink Technology Co.,Ltd
                       '28:23:F5',  # China Mobile (Hangzhou) Information Technology Co., Ltd.
                       '28:57:BE',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '28:82:7C Bosch Automative products(Suzhou)Co.,Ltd',  # Changzhou Branch
                       '28:D9:8A',  # Hangzhou Konke Technology Co.,Ltd.
                       '2C:16:BD:D0',  # Hangzhou Yanzhi Technology Co.,Ltd.
                       '2C:27:9E:00',  # Changzhou WEBO Weighing Device & System CO.,LTD
                       '2C:28:B7',  # Hangzhou Ruiying technology co., LTD
                       '2C:A5:9C',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '30:39:A9',  # Hongshan Information Science and Technology (HangZhou) Co.,Ltd.
                       '30:49:50:B0',  # Hangzhou Ev-Tech Co.,Ltd
                       '30:71:B2',  # Hangzhou Prevail Optoelectronic Equipment Co.,LTD.
                       '30:FF:F6',  # Hangzhou KuoHeng Technology Co.,ltd
                       '34:09:62',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '34:5E:E7',  # Hangzhou ChengFengErLai Digial Technology Co.,Ltd.
                       '34:BD:20',  # Hangzhou Hikrobot Technology Co., Ltd.
                       '34:C1:03',  # Hangzhou Huamu Technology Co.,Ltd.
                       '34:CF:6C',  # Hangzhou Taili wireless communication equipment Co.,Ltd
                       '34:EA:34',  # Hangzhou Gubei Electronics Technology Co.,Ltd
                       '38:22:D6',  # Hangzhou H3C Technologies Co., Limited
                       '38:91:D5',  # Hangzhou H3C Technologies Co., Limited
                       '38:97:D6',  # Hangzhou H3C Technologies Co., Limited
                       '3C:1B:F8',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '3C:1E:13',  # Hangzhou Sunrise Technology Co., Ltd
                       '3C:2C:94',  # 杭州德澜科技有限公司（HangZhou Delan Technology Co.,Ltd）
                       '3C:8A:E5',  # Tensun Information Technology(Hangzhou) Co.,LTD
                       '3C:8C:40',  # Hangzhou H3C Technologies Co., Limited
                       '3C:E5:A6',  # Hangzhou H3C Technologies Co., Limited
                       '40:6A:8E',  # Hangzhou Puwell OE Tech Ltd.
                       '40:AC:BF',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '40:D8:55:00:20',  # Hangzhou Chenxiao Technologies Co. Ltd.
                       '40:ED:98:D0',  # Hangzhou GANX Technology Co.,Ltd.
                       '44:03:77:B0',  # Hangzhou Asia Infrastructure Tech. Co., Ltd.
                       '44:19:B6',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '44:47:CC',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '44:6F:D8:C0',  # Changzhou Haitu Electronic Technology Co.,Ltd
                       '44:A6:42',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '48:0B:B2:40',  # Hangzhou Freely Communication Co., Ltd.
                       '48:7A:DA',  # Hangzhou H3C Technologies Co., Limited
                       '4C:45:76',  # China Mobile(Hangzhou) Information Technology Co.,Ltd.
                       '4C:62:DF',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '4C:91:7A:90',  # Hangzhou Hangtu Technology Co.,Ltd.
                       '4C:BD:8F',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '4C:EA:41:B0',  # Hangzhou Hortwork Technology Co.,Ltd.
                       '4C:F5:DC',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '50:50:CE',  # Hangzhou Dianyixia Communication Technology Co. Ltd.
                       '50:52:D2',  # Hangzhou Telin Technologies Co., Limited
                       '50:DA:00',  # Hangzhou H3C Technologies Co., Limited
                       '50:E5:38',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '50:ED:78',  # Changzhou Yongse Infotech Co.,Ltd
                       '54:8C:81',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '54:9A:11:D0',  # Hangzhou duotin Technology Co., Ltd.
                       '54:C4:15',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '54:D6:0D',  # Hangzhou Ezviz Software Co.,Ltd.
                       '58:03:FB',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '58:50:ED',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '58:66:BA',  # Hangzhou H3C Technologies Co., Limited
                       '58:6A:B1',  # Hangzhou H3C Technologies Co., Limited
                       '58:8F:CF',  # Hangzhou Ezviz Software Co.,Ltd.
                       '58:C8:76',  # China Mobile (Hangzhou) Information Technology Co., Ltd.
                       '58:E8:73',  # Hangzhou DANGBEI NETWORK TECH.Co.,Ltd
                       '58:FD:5D',  # Hangzhou Xinyun technology Co., Ltd.
                       '5C:34:5B',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '5C:DD:70',  # Hangzhou H3C Technologies Co., Limited
                       '5C:F2:86:00',  # Hangzhou Signwei Electronics Technology Co., Ltd
                       '60:0B:03',  # Hangzhou H3C Technologies Co., Limited
                       '60:DA:83',  # Hangzhou H3C Technologies Co., Limited
                       '64:DB:8B',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '64:F2:FB',  # Hangzhou Ezviz Software Co.,Ltd.
                       '68:6D:BC',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '6C:5C:3D:60',  # Hangzhou Netease Yanxuan Trading Co.,Ltd
                       '6C:93:08:80',  # Hangzhou Risco System Co.,Ltd
                       '70:06:92:60',  # Hangzhou Clounix Technology Limited
                       '70:3D:15',  # Hangzhou H3C Technologies Co., Limited
                       '70:B3:D5:1F:40',  # Hangzhou Woosiyuan Communication Co.,Ltd.
                       '70:B3:D5:37:30',  # Hangzhou Weimu Technology Co.,Ltd.
                       '70:B3:D5:4E:C0',  # Hangzhou Youshi Industry Co., Ltd.
                       '70:B3:D5:50:C0',  # Hangzhou landesker digital technology co. LTD
                       '70:B3:D5:5D:E0',  # Hangzhou AwareTec Technology Co., Ltd
                       '70:B3:D5:6A:E0',  # Hangzhou Weimu Technology Co,.Ltd.
                       '70:B3:D5:8B:F0',  # Hangzhou Leaper Technology Co. Ltd.
                       '70:B3:D5:90:A0',  # Hangzhou SunTown Intelligent Science & Technology Co.,Ltd.
                       '70:B3:D5:E8:00',  # Changzhou Rapid Information Technology Co,Ltd
                       '70:B3:D5:ED:50',  # Hangzhou battle link technology Co.,Ltd
                       '70:B3:D5:FE:F0',  # Hangzhou Hualan Microelectronique Co.,Ltd
                       '70:BA:EF',  # Hangzhou H3C Technologies Co., Limited
                       '70:F9:6D',  # Hangzhou H3C Technologies Co., Limited
                       '74:1F:4A',  # Hangzhou H3C Technologies Co., Limited
                       '74:25:8A',  # Hangzhou H3C Technologies Co., Limited
                       '74:3F:C2',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '74:54:6B',  # Hangzhou zhiyi communication co., ltd
                       '78:0F:77',  # Hangzhou Gubei Electronics Technology Co.,Ltd
                       '78:A6:A0',  # Hangzhou Ezviz Software Co.,Ltd.
                       '78:BB:88',  # Maxio Technology (Hangzhou) Ltd.
                       '78:C1:AE',  # Hangzhou Ezviz Software Co.,Ltd.
                       '7C:45:F9:30',  # Hangzhou LUXAR Technologies Co., Ltd
                       '7C:47:7C:B0',  # Hangzhou Yiyitaidi Information Technology Co., Ltd.
                       '7C:CB:E2:70',  # Hangzhou Kaicom Communication Co.,Ltd
                       '7C:CB:E2:90',  # Hangzhou Haohaokaiche Technology Co.,Ltd.
                       '80:44:FD',  # China Mobile (Hangzhou) Information Technology Co., Ltd.
                       '80:76:77',  # Hangzhou puwell cloud tech co., ltd.
                       '80:7B:85:10',  # Hangzhou Synway Information Engineering Co., Ltd
                       '80:7C:62',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '80:BE:AF',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '80:D1:8B',  # Hangzhou I'converge Technology Co.,Ltd
                       '80:F5:AE',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '80:F6:2E',  # Hangzhou H3C Technologies Co., Limited
                       '84:83:19',  # Hangzhou Zero Zero Technology Co., Ltd.
                       '84:9A:40',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '84:D9:31',  # Hangzhou H3C Technologies Co., Limited
                       '84:E0:F4:20',  # Hangzhou Uni-Ubi Co.,Ltd.
                       '84:E0:F4:50',  # Hangzhou Nationalchip Science & Technology Co.,Ltd.
                       '88:70:33',  # Hangzhou Silan Microelectronic Inc
                       '88:A6:EF:50',  # Labpano Technology (Changzhou) Co., Ltd.
                       '8C:18:50',  # China Mobile (Hangzhou) Information Technology Co., Ltd.
                       '8C:1F:64:62:C0',  # Hangzhou EasyXR Advanced Technology Co., Ltd.
                       '8C:E7:48',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '90:38:DF',  # Changzhou Tiannengbo System Co. Ltd.
                       '90:6A:94',  # Hangzhou huacheng network technology co., ltd
                       '90:F1:B0',  # Hangzhou Anheng Info&Tech CO.,LTD
                       '94:CC:04:00',  # Hangzhou Yongkong Technology Co., Ltd.
                       '94:E1:AC',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '98:06:37:30',  # Hangzhou Sanxin Network Technology Co.,Ltd
                       '98:4C:04',  # Zhangzhou Keneng Electrical Equipment Co Ltd
                       '98:6E:E8:D0',  # Changzhou Jiahao Radio&TV device CO.,LTD
                       '98:8B:0A',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '98:8F:E0:80',  # Changzhou Perceptime Technology Co.,Ltd.
                       '98:9D:E5',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '98:DF:82',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '98:F1:12',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       '98:F9:C7:D0',  # Hangzhou soar security technologies limited liability company
                       '9C:06:1B',  # Hangzhou H3C Technologies Co., Limited
                       '9C:1F:CA',  # Hangzhou AlmightyDigit Technology Co., Ltd
                       '9C:82:75',  # Yichip Microelectronics (Hangzhou) Co.,Ltd
                       'A0:19:B2:B0',  # Hangzhou iMagic Technology Co., Ltd
                       'A0:43:B0',  # Hangzhou BroadLink Technology Co.,Ltd
                       'A0:FF:0C',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'A4:14:37',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'A4:4C:62',  # Hangzhou Microimage Software Co., Ltd
                       'A4:C2:AB',  # Hangzhou LEAD-IT Information & Technology Co.,Ltd
                       'A4:D5:C2',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'A4:FB:8D',  # Hangzhou Dunchong Technology Co.Ltd
                       'A8:41:22',  # China Mobile (Hangzhou) Information Technology Co.,Ltd.
                       'AC:3D:75',  # Hangzhou Zhiway Technologies Co.,Ltd.
                       'AC:74:09',  # Hangzhou H3C Technologies Co., Limited
                       'AC:B9:2F',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'AC:CB:51',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'B0:68:B6',  # Hangzhou OYE Technology Co. Ltd
                       'B0:B3:53:60',  # Hangzhou Hikrobot Technology Co., Ltd.
                       'B0:F9:63',  # Hangzhou H3C Technologies Co., Limited
                       'B4:54:59',  # China Mobile (Hangzhou) Information Technology Co., Ltd.
                       'B4:73:56',  # Hangzhou Treebear Networking Co., Ltd.
                       'B4:A2:EB:A0',  # Hengkang（Hangzhou）Co.,Ltd
                       'B4:A3:82',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'B4:BA:12',  # China Mobile (Hangzhou) Information Technology Co.,Ltd.
                       'B4:C1:70',  # Yi chip Microelectronics (Hangzhou) Co., Ltd
                       'BC:34:00:D0',  # Hangzhou Linker Digital Technology Co., Ltd
                       'BC:5E:33',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'BC:74:D7',  # Hangzhou JuRu Technology CO.,LTD
                       'BC:9B:5E',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'BC:AD:28',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'BC:BA:C2',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'BC:D7:CE',  # China Mobile (Hangzhou) Information Technology Co., Ltd.
                       'C0:51:7E',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'C0:56:E3',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'C0:6D:ED',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'C0:DA:74',  # Hangzhou Sunyard Technology Co., Ltd.
                       'C0:EA:C3:30',  # Hangzhou Qixun Technology Co., Ltd
                       'C0:F6:36',  # Hangzhou Kuaiyue Technologies, Ltd.
                       'C0:FB:F9:A0',  # Tiandi(Changzhou) Automation Co., Ltd.
                       'C4:2F:90',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'C4:82:4E',  # Changzhou Uchip Electronics Co., LTD.
                       'C4:CA:D9',  # Hangzhou H3C Technologies Co., Limited
                       'C4:CD:82',  # Hangzhou Lowan Information Technology Co., Ltd.
                       'C8:6B:BC:D0',  # Scantech(Hangzhou)Co.,Ltd
                       'C8:C1:3C',  # Hangzhou Co., Ltd
                       'C8:F7:42',  # Hangzhou Gubei Electronics Technology Co.,Ltd
                       'CC:D3:9D:C0',  # Hangzhou Scooper Technology Co.,Ltd.
                       'CC:E2:36',  # Hangzhou Yaguan Technology Co. LTD
                       'CC:F0:FD',  # China Mobile (Hangzhou) Information Technology Co., Ltd.
                       'D0:5F:64:10',  # Hangzhou ToupTek Photonics Co., Ltd.
                       'D0:D9:4F:90',  # Hangzhou xiaoben technology co.,Ltd
                       'D4:20:00:50',  # Monolith Electric?Changzhou?Co.,Ltd.
                       'D4:43:A8',  # Changzhou Haojie Electric Co., Ltd.
                       'D4:61:FE',  # Hangzhou H3C Technologies Co., Limited
                       'D4:E8:53',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'D8:48:EE',  # Hangzhou Xueji Technology Co., Ltd.
                       'D8:AF:3B',  # Hangzhou Bigbright Integrated communications system Co.,Ltd
                       'DC:07:C1',  # Hangzhou QiYang Technology Co.,Ltd.
                       'DC:07:F8',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'DC:36:43:50',  # Hangzhou Chingan Tech Co., Ltd.
                       'DC:36:43:D0',  # Hangzhou Huanyu Vision Technology Co., Ltd
                       'DC:D2:6A',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'E0:3C:1C:60',  # GhinF Digital information technology (hangzhou) Co., Ltd
                       'E0:3C:1C:B0',  # Hangzhou Uni-Ubi Co.,Ltd.
                       'E0:4B:41',  # Hangzhou Beilian Low Carbon Technology Co., Ltd.
                       'E0:61:B2',  # Hangzhou Zenointel Technology Co., Ltd
                       'E0:BA:AD',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'E0:CA:3C',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'E0:DF:13',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'E4:35:93',  # Hangzhou GoTo technology Co.Ltd
                       'E4:4C:C7:60',  # Hangzhou Ole-Systems Co., Ltd
                       'E4:84:2B',  # Hangzhou Softel Optic Co., Ltd
                       'E8:16:56',  # Hangzhou BroadLink Technology Co.,Ltd
                       'E8:6C:C7:90',  # Hangzhou Lanxum Security Technology Co., Ltd
                       'E8:70:72',  # Hangzhou BroadLink Technology Co.,Ltd
                       'E8:A0:ED',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'EC:0B:AE',  # Hangzhou BroadLink Technology Co.,Ltd
                       'EC:97:E0',  # Hangzhou Ezviz Software Co.,Ltd.
                       'EC:9A:0C:40',  # Hangzhou Saicom Communication Technology Co., LTD
                       'EC:C8:9C',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'EC:DF:C9',  # Hangzhou Microimage Software Co., Ltd
                       'F0:10:AB',  # China Mobile (Hangzhou) Information Technology Co., Ltd.
                       'F0:22:1D:A0',  # Hangzhou Gold Electronic Equipment Co., Ltd
                       'F4:06:A5',  # Hangzhou Bianfeng Networking Technology Co., Ltd.
                       'F8:4D:FC',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'F8:F0:9D',  # Hangzhou Prevail Communication Technology Co., Ltd
                       'FC:61:79:60',  # Hangzhou LiDe Communication Co.,Ltd
                       'FC:9F:FD',  # Hangzhou Hikvision Digital Technology Co.,Ltd.
                       'FC:D2:B6:D0',  # Bee Smart(Changzhou) Information Technology Co., Ltd
                       'FC:E8:92',  # Hangzhou Lancable Technology Co.,Ltd
                       ]

# Zhejiang Dahua Technology MAC prefix
dahua_mac_prefix = ['08:ED:ED',  # Zhejiang Dahua Technology Co., Ltd.
                    '14:A7:8B',  # Zhejiang Dahua Technology Co., Ltd.
                    '24:52:6A',  # Zhejiang Dahua Technology Co., Ltd.
                    '38:AF:29',  # Zhejiang Dahua Technology Co., Ltd.
                    '3C:E3:6B',  # Zhejiang Dahua Technology Co., Ltd.
                    '3C:EF:8C',  # Zhejiang Dahua Technology Co., Ltd.
                    '40:2C:76:10',  # Shanghai Dahua Scale Factory
                    '4C:11:BF',  # Zhejiang Dahua Technology Co., Ltd.
                    '5C:F5:1A',  # Zhejiang Dahua Technology Co., Ltd.
                    '64:FD:29',  # Zhejiang Dahua Technology Co., Ltd.
                    '6C:1C:71',  # Zhejiang Dahua Technology Co., Ltd.
                    '74:C9:29',  # Zhejiang Dahua Technology Co., Ltd.
                    '8C:E9:B4',  # Zhejiang Dahua Technology Co., Ltd.
                    '90:02:A9',  # Zhejiang Dahua Technology Co., Ltd.
                    '98:F9:CC',  # Zhejiang Dahua Technology Co., Ltd.
                    '9C:14:63',  # Zhejiang Dahua Technology Co., Ltd.
                    'A0:BD:1D',  # Zhejiang Dahua Technology Co., Ltd.
                    'B4:4C:3B',  # Zhejiang Dahua Technology Co., Ltd.
                    'BC:32:5F',  # Zhejiang Dahua Technology Co., Ltd.
                    'C0:39:5A',  # Zhejiang Dahua Technology Co., Ltd.
                    'C4:AA:C4',  # Zhejiang Dahua Technology Co., Ltd.
                    'D4:43:0E',  # Zhejiang Dahua Technology Co., Ltd.
                    'E0:2E:FE',  # Zhejiang Dahua Technology Co., Ltd.
                    'E0:50:8B',  # Zhejiang Dahua Technology Co., Ltd.
                    'E4:24:6C',  # Zhejiang Dahua Technology Co., Ltd.
                    'F4:B1:C2',  # Zhejiang Dahua Technology Co., Ltd.
                    'FC:5F:49',  # Zhejiang Dahua Technology Co., Ltd.
                    'FC:B6:9D',  # Zhejiang Dahua Technology Co., Ltd.
                    ]

# Combine the list
mac_prefix_list = zte_mac_prefix + huawei_mac_prefix + hytera_mac_prefix + hangzhou_mac_prefix + dahua_mac_prefix

for mac_prefix in mac_prefix_list:
    data = snipe_api.call('hardware', {'search': mac_prefix})
    for result in data['rows']:
        for custom_field in result['custom_fields'].values():
            if custom_field['field_format'] != "MAC" or not custom_field['value']:
                continue
            if str(custom_field['value']).startswith(mac_prefix):
                print(f"{mac_prefix} - {result['name']}")
