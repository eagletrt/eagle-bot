import httpx
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
        self._session = httpx.AsyncClient()
        self._session.headers.update({
            # NocoDB expects the API key in the 'xc-token' header
            'xc-token': api_key,
            'Content-Type': 'application/json'
        })

    async def tags(self, kind: str) -> list[str]:
        """ Return all tags for the given kind. """

        # fetch all records from the relevant table, requesting only the Tag field
        res = await self._session.get(
            f"{self.base_url}/api/v2/tables/{config['NocoDB'][kind]['table']}/records",
            params={"limit": 1000, "fields": "Tag"}
        )
        res.raise_for_status()
        items = res.json().get("list")
        if not items:
            return []
        return [f"@{item['Tag'].lower().strip()}" for item in items]

    async def members(self, tag: str, kind: str) -> list[str]:
        """ Return Telegram usernames for the given tag and kind. """

        # find the NocoDB internal Id for the record that matches the tag
        nocoid_res = await self._session.get(
            f"{self.base_url}/api/v2/tables/{config['NocoDB'][kind]['table']}/records",
            params={"limit": 1000, "where": f"(Tag,like,{tag})", "fields": "Id"}
        )
        nocoid_res.raise_for_status()
        nocoid = nocoid_res.json().get("list")[0].get("Id")

        # fetch linked member records for that record via the link endpoint
        res = await self._session.get(
            f"{self.base_url}/api/v2/tables/{config['NocoDB'][kind]['table']}/links/{config['NocoDB'][kind]['link']}/records/{nocoid}",
            params={"limit": 1000}
        )
        res.raise_for_status()
        res = res.json().get("list")
        if not res:
            return []

        member_ids = [str(item["Id"]) for item in res]

        # fetch member records by Id and request only the Telegram Username field
        params = {
            "limit": 1000,
            "where": f"(Id,in,{','.join(member_ids)})",
            "fields": "Telegram Username",
            "viewId": config['NocoDB']['members']["view"] # use view to filter out inactive members
        }

        res = await self._session.get(
            f"{self.base_url}/api/v2/tables/{config['NocoDB']['members']['table']}/records",
            params=params
        )

        items = res.json().get("list")
        return [item["Telegram Username"] for item in items if item.get("Telegram Username")]

    async def email_from_username(self, username: str) -> str:
        """ Lookup the Team Email for a given Telegram username. """

        res = await self._session.get(
            f"{self.base_url}/api/v2/tables/{config['NocoDB']['members']['table']}/records",
            params={
                "limit": 1000,
                "where": f"(Telegram Username,like,@{username})~or(Telegram Username,like,{username})",
                "fields": "Team Email"
            }
        )
        res.raise_for_status()
        items = res.json().get("list")

        # if items found return Team Email (or empty string if field missing), else None
        return items[0].get("Team Email", "") if items else None

    async def username_from_email(self, email: str) -> str:
        """ Lookup the Telegram Username for a given Team Email. """

        res = await self._session.get(
            f"{self.base_url}/api/v2/tables/{config['NocoDB']['members']['table']}/records",
            params={
                "limit": 1000,
                "where": f"(Team Email,eq,{email})",
                "fields": "Telegram Username"
            }
        )
        res.raise_for_status()
        items = res.json().get("list")
        return items[0].get("Telegram Username", "") if items else None

    async def quiz_answer_log(self, username: str, is_correct: bool) -> None:
        """ Log a question answer attempt for the given username. """

        table = config['NocoDB']['quiz']['table']
        url = f"{self.base_url}/api/v2/tables/{table}/records"

        # Find existing record for the username
        find_params = {
            "where": f"(username,eq,{username})",
            "fields": "Id,answered,correct",
            "limit": 1
        }
        res = await self._session.get(url, params=find_params)
        res.raise_for_status()
        records = res.json().get("list", [])

        if records:
            # User exists, update their stats
            record = records[0]
            record_id = record['Id']

            payload = {
                "Id": record_id,
                "answered": record.get('answered', 0) + 1,
                "correct": record.get('correct', 0) + (1 if is_correct else 0)
            }

            update_res = await self._session.patch(f"{url}", json=payload)
            update_res.raise_for_status()
        else:
            # User does not exist, create a new record
            payload = {
                "username": username,
                "answered": 1,
                "correct": 1 if is_correct else 0
            }
            create_res = await self._session.post(url, json=payload)
            create_res.raise_for_status()
