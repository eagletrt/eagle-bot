import requests

class ShlinkAPI:
    """ Simple API client that keeps a persistent requests.Session. """
    def __init__(self, base_url: str,):
        """ Initialize the ShlinkAPI client with the given base URL. """

        # Normalize base_url by removing any trailing slash so later joins are consistent
        self.base_url = base_url.rstrip("/")

        # Create a Session to reuse TCP connections and carry default headers/cookies
        self._session = requests.Session()

        # Set default headers for JSON APIs. Individual requests can override this.
        self._session.headers.update({
            'Content-Type': 'application/json'
        })