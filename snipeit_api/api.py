from __future__ import annotations

import logging
from sys import exit
from datetime import timedelta
from time import sleep
from typing import Any

from requests_cache import CachedSession

session = CachedSession(
    'snipeit_cache',  # Use a custom cache dir
    backend='memory',  # Use an in-memory cache
    expire_after=timedelta(hours=1),  # Cache for 1 day
    allowable_codes=[200],  # Cache only successful responses
    allowable_methods=['GET']  # Cache only GET requests
)


class SnipeApiError(Exception):
    def __init__(self, message, data):
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
        self.headers = {
            'Authorization': f"Bearer {api_key}",
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if headers:
            self.headers.update(headers)

    def search(self, search_string: str, endpoint: str, page: int = 0) -> dict:
        if not search_string:
            return {'rows': [], 'total': 0}

        logging.debug(f"Searching for {search_string} in {endpoint}")

        payload = {
            'search': search_string,
            'limit': self.page_size,
            'offset': page * self.page_size
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
        endpoint = self._map_endpoint(endpoint)
        api_url = f"{self.url}/api/v1/{endpoint}"

        if method != "GET":
            self._expire_cache(api_url)

        # Snipe-IT API does not understand JSON with GET requests
        if method == "GET" and payload:
            api_url = self._build_get_url(api_url, payload)
            payload = None

        logging.debug(f"Calling Snipe-IT URL: {api_url}")

        try:
            response = session.request(method, api_url, auth=None, headers=self.headers, json=payload,
                                       verify=self.verify_tls)
        except ConnectionError:
            return self._handle_connection_error(endpoint, payload, method)

        if 200 <= response.status_code < 300:
            self._reset_backoff()
            return response.json()

        return self._handle_connection_error(endpoint, payload, method)

    def _map_endpoint(self, endpoint: str) -> str:
        endpoint_map = {
            "category": "categories",
            "company": "companies",
        }
        # See if endpoint starts with a mapped endpoint
        for key, value in endpoint_map.items():
            if endpoint.startswith(key):
                return endpoint.replace(key, value)
        return endpoint

    def _expire_cache(self, api_url: str) -> None:
        expiring_urls = list(filter(lambda x: x.startswith(api_url), session.cache.urls()))
        session.cache.delete(urls=expiring_urls)

    def _build_get_url(self, api_url: str, payload: dict) -> str:
        api_url += "?" + "&".join(f"{key}={value}" for key, value in payload.items())
        return api_url

    def _handle_connection_error(self, endpoint: str, payload: Any, method: str) -> Any:
        logging.error("Connection error, waiting to see if it resolves")
        if self.snipe_backoff > 5:
            logging.error(f"Connection error persists, with {method} to {endpoint} exiting")
            logging.debug(payload)
            exit(2)
        self.snipe_backoff += 1
        sleep(self.snipe_backoff_seconds * self.snipe_backoff)
        return self.call(endpoint, payload, method)

    def _reset_backoff(self) -> None:
        if self.snipe_backoff > 0:
            self.snipe_backoff -= 1