"""
API client for interacting with Eagle's lab endpoints.

This module defines a small wrapper around requests.Session to call
two endpoints: /lab/ore and /lab/inlab.
"""

import requests

class EagleAPI:
    """
    Simple API client that keeps a persistent requests.Session.

    Args:
        base_url (str): Base URL of the Eagle service (e.g. "https://example.com").
                        Trailing slashes are normalized away.
    """
    def __init__(self, base_url: str,):
        # Normalize base_url by removing any trailing slash so later joins are consistent
        self.base_url = base_url.rstrip("/")

        # Create a Session to reuse TCP connections and carry default headers/cookies
        self._session = requests.Session()

        # Set default headers for JSON APIs. Individual requests can override this.
        self._session.headers.update({
            'Content-Type': 'application/json'
        })

    def oreLab(self, username: str) -> dict:
        """
        Call the ore lab endpoint for a given username.

        Performs a GET request to: {base_url}/lab/ore
        Query parameters:
            - username: the username to query

        Returns:
            dict: Parsed JSON response from the server.

        Notes:
            - This will raise requests.RequestException on network errors.
            - If the response body is not valid JSON, res.json() will raise a ValueError.
        """
        # Perform the GET request with the username as a query parameter
        res = self._session.get(f"{self.base_url}/lab/ore", params={
            "username": username
        })

        # Parse and return JSON body (may raise if response is not JSON)
        return res.json()

    def inlab(self) -> dict:
        """
        Call the inlab endpoint.

        Performs a GET request to: {base_url}/lab/inlab

        Returns:
            dict: Parsed JSON response from the server.

        Notes:
            - Same exception behavior as oreLab regarding network/JSON errors.
        """
        # Call the endpoint without query parameters
        res = self._session.get(f"{self.base_url}/lab/inlab")

        # Return parsed JSON result
        return res.json()
