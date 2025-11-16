import requests
import qrcode
import io

class ShlinkAPI:
    """ Simple API client that keeps a persistent requests.Session. """
    def __init__(self, base_url: str, api_key: str):
        """ Initialize the ShlinkAPI client with the given base URL. """

        # Normalize base_url by removing any trailing slash so later joins are consistent
        self.base_url = base_url.rstrip("/")

        # Create a Session to reuse TCP connections and carry default headers/cookies
        self._session = requests.Session()

        # Set default headers for JSON APIs. Individual requests can override this.
        self._session.headers.update({
            'X-Api-Key': api_key,
            'Content-Type': 'application/json'
        })

    def generate_qr_code(self, url: str) -> io.BytesIO:
        """ Generate a QR code for the given URL. """

        img = qrcode.make(url)
        
        # Save the QR code image to a BytesIO buffer
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        buf.seek(0)
        return buf

        
    def generate_short_url(self, url: str, custom_code: str = None) -> str:
        """ Generate a short URL for the given URL, optionally with a custom code. """

        payload = {
            "longUrl": url
        }
        if custom_code:
            payload["customSlug"] = custom_code

        response = self._session.post(f"{self.base_url}/rest/v3/short-urls", json=payload)
        response.raise_for_status()

        data = response.json()
        return data['shortUrl']