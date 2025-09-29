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

        def area_tags(self) -> list[str]:
                """
                Fetch all area tags from the areas table.

                Returns:
                - list of tag strings formatted as "@tag" (lowercased and stripped).
                """
                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/mbftgdmmi4t668c/records",
                        params={"limit": 1000, "fields": "Tag"}
                )
                # API returns an object with "list" key containing records
                items = res.json().get("list")
                # format each Tag value as @lowercase
                return [f"@{item['Tag'].lower().strip()}" for item in items]

        def workgroup_tags(self) -> list[str]:
                """
                Fetch all workgroup tags from the workgroups table.

                Returns:
                - list of tag strings formatted as "@tag" (lowercased and stripped).
                """
                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/m5gpr28sp047j7w/records",
                        params={"limit": 1000, "fields": "Tag"}
                )
                items = res.json().get("list")
                return [f"@{item['Tag'].lower().strip()}" for item in items]

        def project_tags(self) -> list[str]:
                """
                Fetch all project tags from the projects table.

                Returns:
                - list of tag strings formatted as "@tag" (lowercased and stripped).
                """
                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/ma3scczigje9u17/records",
                        params={"limit": 1000, "fields": "Tag"}
                )
                items = res.json().get("list")
                return [f"@{item['Tag'].lower().strip()}" for item in items]

        def role_tags(self) -> list[str]:
                """
                Fetch all role tags from the roles table.

                Returns:
                - list of tag strings formatted as "@tag" (lowercased and stripped).
                """
                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/mpur65wgd6gqi98/records",
                        params={"limit": 1000, "fields": "Tag"}
                )
                items = res.json().get("list")
                return [f"@{item['Tag'].lower().strip()}" for item in items]

        def area_members(self, tag: str) -> list[str]:
                """
                Given an area tag (exact tag string expected by the API query), return Telegram usernames
                of members who belong to that area.

                Steps:
                1. Query the areas table to find the record Id that matches the tag.
                2. Query the linked-members link table for that area Id to get member Ids.
                3. Query the members table for those Ids and return the "Telegram Username" field.

                Returns:
                - list of Telegram usernames (strings). Filters out records missing the field.

                Raises:
                - IndexError/KeyError if the tag lookup returns no records or API response shape changes.
                - requests.RequestException for network/API errors.
                """
                # find the NocoDB internal Id for the area with the provided tag
                nocoid = self._session.get(
                        f"{self.base_url}/api/v2/tables/mbftgdmmi4t668c/records",
                        params={"limit": 1000, "where": f"(Tag,like,{tag})", "fields": "Id"}
                ).json().get("list")[0].get('Id')

                # fetch linked member records for that area via the link endpoint
                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/mbftgdmmi4t668c/links/cjest7m9j409yia/records/{nocoid}",
                        params={"limit": 1000}
                ).json().get("list")

                # collect member Ids as strings for the next query's IN clause
                member_ids = [str(item['Id']) for item in res]

                # fetch member records by Id and request only the Telegram Username field
                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/m3rsrrmnhhxxw0p/records",
                        params={
                                "limit": 1000,
                                "where": f"(Id,in,{','.join(member_ids)})",
                                "fields": "Telegram Username",
                                # viewId narrows which records are returned (project-specific view)
                                "viewId": "vw72nyx0bmaak96s"
                        }
                )

                items = res.json().get("list")
                # return only entries that have a Telegram Username value
                return [item['Telegram Username'] for item in items if item.get('Telegram Username')]

        def workgroup_members(self, tag: str) -> list[str]:
                """
                Same flow as area_members but for workgroups.

                Table and link IDs are different and specific to the NocoDB schema used.
                """
                nocoid = self._session.get(
                        f"{self.base_url}/api/v2/tables/m5gpr28sp047j7w/records",
                        params={"limit": 1000, "where": f"(Tag,like,{tag})", "fields": "Id"}
                ).json().get("list")[0].get('Id')

                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/m5gpr28sp047j7w/links/c4olgvricf9nalu/records/{nocoid}",
                        params={"limit": 1000}
                ).json().get("list")

                member_ids = [str(item['Id']) for item in res]
                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/m3rsrrmnhhxxw0p/records",
                        params={
                                "limit": 1000,
                                "where": f"(Id,in,{','.join(member_ids)})",
                                "fields": "Telegram Username",
                                "viewId": "vw72nyx0bmaak96s"
                        }
                )

                items = res.json().get("list")
                return [item['Telegram Username'] for item in items if item.get('Telegram Username')]

        def project_members(self, tag: str) -> list[str]:
                """
                Same flow as area_members but for projects.

                Returns Telegram usernames of project members.
                """
                nocoid = self._session.get(
                        f"{self.base_url}/api/v2/tables/ma3scczigje9u17/records",
                        params={"limit": 1000, "where": f"(Tag,like,{tag})", "fields": "Id"}
                ).json().get("list")[0].get('Id')

                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/ma3scczigje9u17/links/c96a46tetiedgvg/records/{nocoid}",
                        params={"limit": 1000}
                ).json().get("list")

                member_ids = [str(item['Id']) for item in res]
                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/m3rsrrmnhhxxw0p/records",
                        params={
                                "limit": 1000,
                                "where": f"(Id,in,{','.join(member_ids)})",
                                "fields": "Telegram Username",
                                "viewId": "vw72nyx0bmaak96s"
                        }
                )

                items = res.json().get("list")
                return [item['Telegram Username'] for item in items if item.get('Telegram Username')]

        def role_members(self, tag: str) -> list[str]:
                """
                Same flow as area_members but for roles.

                Returns Telegram usernames of role members.
                """
                nocoid = self._session.get(
                        f"{self.base_url}/api/v2/tables/mpur65wgd6gqi98/records",
                        params={"limit": 1000, "where": f"(Tag,like,{tag})", "fields": "Id"}
                ).json().get("list")[0].get('Id')

                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/mpur65wgd6gqi98/links/cbuvnbm0wxwkfyo/records/{nocoid}",
                        params={"limit": 1000}
                ).json().get("list")

                member_ids = [str(item['Id']) for item in res]
                res = self._session.get(
                        f"{self.base_url}/api/v2/tables/m3rsrrmnhhxxw0p/records",
                        params={
                                "limit": 1000,
                                "where": f"(Id,in,{','.join(member_ids)})",
                                "fields": "Telegram Username",
                                "viewId": "vw72nyx0bmaak96s"
                        }
                )

                items = res.json().get("list")
                return [item['Telegram Username'] for item in items if item.get('Telegram Username')]

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
