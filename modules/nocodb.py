"""
nocodb.py

Lightweight wrapper around a NocoDB instance used by the eagle-bot project.

This module provides:
- NocoDB: a small client that queries specific tables/links in a NocoDB API.
- Methods to list tags (areas, workgroups, projects, roles).
- Methods to resolve members for a given tag (returning Telegram usernames).
- Helpers to map between Telegram username and team email.

Notes:
- Uses requests.Session for connection reuse and to set the 'xc-token' header for auth.
- Assumes specific table IDs and link IDs hard-coded in the queries.
- No advanced error handling is implemented — network or API errors will raise requests exceptions
        or KeyError/IndexError if the API response shape differs.
"""

import requests


class NocoDB:
        """
        Minimal client for querying specific tables in a NocoDB instance.

        Parameters:
        - base_url (str): Base URL of the NocoDB instance (e.g. "https://noco.example.com").
                                        A trailing slash will be removed automatically.
        - api_key (str): API key to be sent in the 'xc-token' header.

        The client sets a JSON content type header and reuses a requests.Session.
        """

        def __init__(self, base_url: str, api_key: str):
                # store base url without trailing slash to make URL composition predictable
                self.base_url = base_url.rstrip("/")

                # reuse a session for connection pooling and consistent headers
                self._session = requests.Session()
                self._session.headers.update({
                        # NocoDB expects the API key in the 'xc-token' header
                        'xc-token': api_key,
                        # we're fetching JSON resources
                        'Content-Type': 'application/json'
                })

        def _tags_for_table(self, table_id: str) -> list[str]:
                """
                Generic helper to fetch Tag values from a given table and format them as "@tag".
                """
                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/{table_id}/records",
                        params={"limit": 1000, "fields": "Tag"}
                )
                items = res.json().get("list")
                return [f"@{item['Tag'].lower().strip()}" for item in items]

        # Convenience wrappers to preserve the original public API while reusing the generic helper
        def area_tags(self) -> list[str]:
                return self._tags_for_table("mbftgdmmi4t668c")
        def workgroup_tags(self) -> list[str]:
                return self._tags_for_table("m5gpr28sp047j7w")
        def project_tags(self) -> list[str]:
                return self._tags_for_table("ma3scczigje9u17")
        def role_tags(self) -> list[str]:
                return self._tags_for_table("mpur65wgd6gqi98")

        def members(self, tag: str, kind: str) -> list[str]:
                """
                Return Telegram usernames for the given tag and kind.

                Parameters:
                - tag: the tag string to look up (same format as used previously, e.g. "@area")
                - kind: one of "area", "workgroup", "project", "role"

                The function unifies the previous area_members, workgroup_members,
                project_members and role_members implementations using an internal
                mapping of table/link/view IDs.
                """
                mapping = {
                        "area": {
                                "table": "mbftgdmmi4t668c",
                                "link": "cjest7m9j409yia",
                                "view": "vw72nyx0bmaak96s"
                        },
                        "workgroup": {
                                "table": "m5gpr28sp047j7w",
                                "link": "c4olgvricf9nalu",
                                "view": "vw72nyx0bmaak96s"
                        },
                        "project": {
                                "table": "ma3scczigje9u17",
                                "link": "c96a46tetiedgvg",
                                "view": "vw72nyx0bmaak96s"
                        },
                        "role": {
                                "table": "mpur65wgd6gqi98",
                                "link": "cbuvnbm0wxwkfyo",
                                "view": "vw72nyx0bmaak96s"
                        }
                }

                if kind not in mapping:
                        raise ValueError(f"unsupported kind: {kind}")

                info = mapping[kind]
                # find the NocoDB internal Id for the record that matches the tag
                nocoid = self._session.get(
                        f"{self.base_url}/api/v2/tables/{info['table']}/records",
                        params={"limit": 1000, "where": f"(Tag,like,{tag})", "fields": "Id"}
                ).json().get("list")[0].get("Id")

                # fetch linked member records for that record via the link endpoint
                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/{info['table']}/links/{info['link']}/records/{nocoid}",
                        params={"limit": 1000}
                ).json().get("list")

                member_ids = [str(item["Id"]) for item in res]

                # fetch member records by Id and request only the Telegram Username field
                params = {
                        "limit": 1000,
                        "where": f"(Id,in,{','.join(member_ids)})",
                        "fields": "Telegram Username"
                }
                if info.get("view"):
                        params["viewId"] = info["view"]

                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/m3rsrrmnhhxxw0p/records",
                        params=params
                )

                items = res.json().get("list")
                return [item["Telegram Username"] for item in items if item.get("Telegram Username")]

        def email_from_username(self, username: str) -> str:
                """
                Lookup the Team Email for a given Telegram username.

                The 'where' clause attempts two matches:
                - Telegram Username like @username
                - Telegram Username like username

                Returns:
                - Team Email string if found.
                - None if no matching record exists.

                Note:
                - The method returns None when no items are found, otherwise it returns a string.
                """
                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/m3rsrrmnhhxxw0p/records",
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
                """
                Lookup the Telegram Username for a given Team Email.

                Returns:
                - Telegram Username string if found.
                - None if no matching record exists (function returns None when items list is empty).
                """
                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/m3rsrrmnhhxxw0p/records",
                        params={
                                "limit": 1000,
                                "where": f"(Team Email,eq,{email})",
                                "fields": "Telegram Username"
                        }
                )
                items = res.json().get("list")
                return items[0].get("Telegram Username", "") if items else None
