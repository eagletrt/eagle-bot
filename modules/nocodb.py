import requests
import tomllib
import logging

# Load configuration from config.ini
with open("data/config.ini", "rb") as f:
    try:
        config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logging.error(f"modules/nocodb - Error parsing data/config.ini: {e}")
        exit(1)

class NocoDB:
    """ Minimal client for querying specific tables in a NocoDB instance. """

    def __init__(self, base_url: str, api_key: str):
        """ Initialize the NocoDB client with base URL and API key. """

        # store base url without trailing slash to make URL composition predictable
        self.base_url = base_url.rstrip("/")

        # reuse a session for connection pooling and consistent headers
        self._session = requests.Session()
        self._session.headers.update({
            # NocoDB expects the API key in the 'xc-token' header
            'xc-token': api_key,
            'Content-Type': 'application/json'
        })

    def tags(self, kind: str) -> list[str]:
        """ Return all tags for the given kind. """

        # fetch all records from the relevant table, requesting only the Tag field
        res = self._session.get(
            f"{self.base_url}/api/v2/tables/{config['NocoDB'][kind]['table']}/records",
            params={"limit": 1000, "fields": "Tag"}
        )
        items = res.json().get("list")
        return [f"@{item['Tag'].lower().strip()}" for item in items]

    def members(self, tag: str, kind: str) -> list[str]:
        """ Return Telegram usernames for the given tag and kind. """

        # find the NocoDB internal Id for the record that matches the tag
        nocoid = self._session.get(
            f"{self.base_url}/api/v2/tables/{config['NocoDB'][kind]['table']}/records",
            params={"limit": 1000, "where": f"(Tag,like,{tag})", "fields": "Id"}
        ).json().get("list")[0].get("Id")

        # fetch linked member records for that record via the link endpoint
        res = self._session.get(
            f"{self.base_url}/api/v2/tables/{config['NocoDB'][kind]['table']}/links/{config['NocoDB'][kind]['link']}/records/{nocoid}",
            params={"limit": 1000}
        ).json().get("list")

        member_ids = [str(item["Id"]) for item in res]

        # fetch member records by Id and request only the Telegram Username field
        params = {
            "limit": 1000,
            "where": f"(Id,in,{','.join(member_ids)})",
            "fields": "Telegram Username",
            "viewId": config['NocoDB']['members']["view"] # use view to filter out inactive members
        }

        res = self._session.get(
            f"{self.base_url}/api/v2/tables/{config['NocoDB']['members']['table']}/records",
            params=params
        )

        items = res.json().get("list")
        return [item["Telegram Username"] for item in items if item.get("Telegram Username")]

    def email_from_username(self, username: str) -> str:
        """ Lookup the Team Email for a given Telegram username. """

        res = self._session.get(
            f"{self.base_url}/api/v2/tables/{config['NocoDB']['members']['table']}/records",
            params={
                "limit": 1000,
                "where": f"(Telegram Username,like,@{username})~or(Telegram Username,like,{username})",
                "fields": "Team Email"
            }
        )
        items = res.json().get("list")

        # if items found return Team Email (or empty string if field missing), else None
        return items[0].get("Team Email", "") if items else None

    def username_from_email(self, email: str) -> str:
        """ Lookup the Telegram Username for a given Team Email. """

        res = self._session.get(
            f"{self.base_url}/api/v2/tables/{config['NocoDB']['members']['table']}/records",
            params={
                "limit": 1000,
                "where": f"(Team Email,eq,{email})",
                "fields": "Telegram Username"
            }
        )
        items = res.json().get("list")
        return items[0].get("Telegram Username", "") if items else None
