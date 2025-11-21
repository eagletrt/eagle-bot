import requests

class EagleAPI:
    """ Simple API client that keeps a persistent requests.Session. """
    def __init__(self, base_url: str,):
        """ Initialize the EagleAPI client with the given base URL. """

        # Normalize base_url by removing any trailing slash so later joins are consistent
        self.base_url = base_url.rstrip("/")

        # Create a Session to reuse TCP connections and carry default headers/cookies
        self._session = requests.Session()

        # Set default headers for JSON APIs. Individual requests can override this.
        self._session.headers.update({
            'Content-Type': 'application/json'
        })

    def oreLab(self, username: str) -> dict:
        """ Call the ore lab endpoint for a given username. """

        # Perform the GET request with the username as a query parameter
        res = self._session.get(f"{self.base_url}/lab/ore", params={
            "username": username
        })

        # Parse and return JSON body (may raise if response is not JSON)
        return res.json()

    def inlab(self) -> dict:
        """ Call the inlab endpoint. """

        # Call the endpoint without query parameters
        res = self._session.get(f"{self.base_url}/lab/inlab")

        # Return parsed JSON result
        return res.json()
