import requests
from ansible2snipe import CONFIG

url = f"{CONFIG['snipe-it']['url']}/api/v1/companies"

names = ["Company 1", "Company 2"]

apikey = CONFIG['snipe-it']['apikey']

headers = {
    "accept": "application/json",
    "content-device_type": "application/json",
    "authorization": f"Bearer {apikey}"
}

for name in names:
    payload = {"name": name}
    response = requests.post(url, json=payload, headers=headers)
    print(response.text)
