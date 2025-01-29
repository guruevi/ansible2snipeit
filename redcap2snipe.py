#!/usr/bin/env python3
import requests

config = dict(
    api_super_token = 'ABCD1234ABCD1234ABCD1234ABCD1234ABCD1234ABCD1234ABCD1234ABCD1234',
    api_token       = '12340DCA87C457B6FABC8147AD7E4790',
    api_url         = 'http://example.com/redcap/api/'
)

fields = {
    'token': config['api_token'],
    'content': 'record',
    'format': 'json',
    'type': 'flat'
}

r = requests.post(config['api_url'],data=fields)
print('HTTP Status: ' + str(r.status_code))
print(r.text)