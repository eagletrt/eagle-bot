import requests


class EagleAPI:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({
            'Authorization': f'{api_key}',
            'Content-Type': 'application/json'
        })

    def oreLab(self, username: str) -> dict:
        res = self._session.get(f"{self.base_url}/api/v2/lab/ore", params={
            "username": username
        })
        return res.json()

    def inlab(self) -> dict:
        res = self._session.get(f"{self.base_url}/api/v2/lab/inlab")
        return res.json()
