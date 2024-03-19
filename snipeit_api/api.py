from __future__ import annotations

import logging
from datetime import timedelta
from time import sleep
from typing import Any

from requests import request
from requests_cache import CachedSession

session = CachedSession(
    'snipeit_cache',  # Use a custom cache dir
    backend='memory',  # Use an in-memory cache
    expire_after=timedelta(days=1),  # Cache for 1 day
    allowable_codes=[200],  # Cache only successful responses
    allowable_methods=['GET']  # Cache only GET requests
)


# Make a Class for the API
class SnipeApiError(Exception):
    def __init__(self, message, data):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        logging.error(f"API Error: {message}")
        logging.debug("API Error Data:")
        logging.debug(data)


class SnipeITApi:
    def __repr__(self):
        return f"SnipeITApi({self.url})"

    def __init__(self, url: str = "", api_key: str = "", page_size=500, headers: dict = None,
                 verify_tls: bool = True) -> None:
        """
        @param url: URL of the Snipe-IT server
        @param verify_tls: Whether to verify the TLS certificate
        @param api_key: API key for Snipe-IT
        @param headers: Additional headers to send to Snipe-IT
        """
        self.url = url
        self.verify_tls = verify_tls
        self.snipe_backoff = 0
        self.snipe_backoff_seconds = 30
        self.page_size = page_size
        self.headers = {'Authorization': f"Bearer {api_key}",
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'}

        if headers:
            self.headers.update(headers)

    def search(self, search_string: str, endpoint: str, page: int = 0) -> dict:
        if not search_string:
            return {'rows': [], 'total': 0}

        logging.debug(f"Searching for {search_string} in {endpoint}")

        page_size = self.page_size
        payload = {
            'search': search_string,
            'limit': page_size,
            'offset': page * page_size
        }

        response = self.call(endpoint, method="GET", payload=payload)

        if 'total' not in response:
            raise SnipeApiError("Invalid response from Snipe-IT", response)

        if response['total'] > payload['limit'] + payload['offset']:
            response['rows'].extend(self.search(search_string, endpoint, page + 1)['rows'])

        logging.debug(f"Found {response['total']} results for {search_string}")
        logging.debug(response['rows'])

        return response

    def call(self, endpoint: str, payload: Any = None, method: str = "GET") -> Any:
        """
        @param endpoint: Which API endpoint to use (eg. devices)
        @param payload: Values to send to Snipe-IT
        @param method: GET, POST, PATCH, DELETE
        @return: Response object from Snipe-IT or raises HTTPError
        """
        logging.debug(f"Calling Snipe-IT API: {endpoint}")
        # replace the endpoint with the correct name
        endpoint_map = {
            "category": "categories",
            "company": "companies",
        }
        # Replace the endpoint with the correct name if part of the URL is in the map
        for key, value in endpoint_map.items():
            if key in endpoint:
                endpoint = endpoint.replace(key, value)

        api_url = f"{self.url}/api/v1/{endpoint}"

        # If method is not GET, expire the cache for this endpoint
        if method != "GET":
            session.cache.delete(expired=True)
            # Get all the keys that match the URL
            cached_urls = session.cache.urls()
            # Filter out cache keys that match part of the URL
            cached_urls = list(filter(lambda x: x.startswith(api_url), cached_urls))
            session.cache.delete(urls=cached_urls)

        # Snipe-IT API does not understand JSON with GET requests
        if method == "GET" and payload:
            api_url += "?"
            for key, value in payload.items():
                api_url += f"{key}={value}&"
            api_url = api_url[:-1]
            payload = None

        logging.debug(f"Calling Snipe-IT URL: {api_url}")

        response = session.request(method, api_url, auth=None, headers=self.headers, json=payload,
                                   verify=self.verify_tls)

        # DEV: This is a lot of output
        # logging.debug(f"Got a response from Snipe-IT: {response.text}")

        if response.status_code >= 200 or response.status_code < 300:
            if self.snipe_backoff > 0:
                self.snipe_backoff -= 1
            # DEV: This is a lot of output
            # logging.debug(f"Got a valid response from Snipe-IT: {response.text}")
            return response.json()

        if response.status_code == 429:
            self.snipe_backoff += 1
            backoff = self.snipe_backoff * self.snipe_backoff_seconds
            logging.warning(f'Snipe-IT ratelimit exceeded: pausing {backoff}s')
            sleep(backoff)
            logging.info("Finished waiting. Retrying lookup...")
            return self.call(endpoint, payload, method)

        logging.error(f"Snipe-IT responded with error code:{response.text}")
        logging.debug(f"{response.status_code} - {response.content}")
        return response.raise_for_status()
