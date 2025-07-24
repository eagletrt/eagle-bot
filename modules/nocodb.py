import requests


class NocoDB:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({
            'xc-token': api_key,
            'Content-Type': 'application/json'
        })

    def area_tags(self) -> list[str]:
        res = self._session.get(f"{self.base_url}/api/v2/tables/mbftgdmmi4t668c/records", params={
            "limit": 1000,
            "fields": "Tag"
        })
        items = res.json().get("list")
        return [f"@{item['Tag'].lower().strip()}" for item in items]

    def workgroup_tags(self) -> list[str]:
        res = self._session.get(f"{self.base_url}/api/v2/tables/m5gpr28sp047j7w/records", params={
            "limit": 1000,
            "fields": "Tag"
        })
        items = res.json().get("list")
        return [f"@{item['Tag'].lower().strip()}" for item in items]

    def project_tags(self) -> list[str]:
        res = self._session.get(f"{self.base_url}/api/v2/tables/ma3scczigje9u17/records", params={
            "limit": 1000,
            "fields": "Tag"
        })
        items = res.json().get("list")
        return [f"@{item['Tag'].lower().strip()}" for item in items]

    def role_tags(self) -> list[str]:
        res = self._session.get(f"{self.base_url}/api/v2/tables/mpur65wgd6gqi98/records", params={
            "limit": 1000,
            "fields": "Tag"
        })
        items = res.json().get("list")
        return [f"@{item['Tag'].lower().strip()}" for item in items]

    def area_members(self, tag: str) -> list[str]:
        nocoid = self._session.get(f"{self.base_url}/api/v2/tables/mbftgdmmi4t668c/records", params={
            "limit": 1000,
            "where": f"(Tag,like,{tag})",
            "fields": "Id"
        }).json().get("list")[0].get('Id')

        res = self._session.get(f"{self.base_url}/api/v2/tables/mbftgdmmi4t668c/links/cjest7m9j409yia/records/{nocoid}", params={
            "limit": 1000
        }).json().get("list")

        member_ids = [str(item['Id']) for item in res]
        res = self._session.get(f"{self.base_url}/api/v2/tables/m3rsrrmnhhxxw0p/records", params={
            "limit": 1000,
            "where": f"(Id,in,{','.join(member_ids)})",
            "fields": "Telegram Username",
            "viewId": "vw72nyx0bmaak96s"
        })

        items = res.json().get("list")
        return [item['Telegram Username'] for item in items if item.get('Telegram Username')]

    def workgroup_members(self, tag: str) -> list[str]:
        nocoid = self._session.get(f"{self.base_url}/api/v2/tables/m5gpr28sp047j7w/records", params={
            "limit": 1000,
            "where": f"(Tag,like,{tag})",
            "fields": "Id"
        }).json().get("list")[0].get('Id')

        res = self._session.get(f"{self.base_url}/api/v2/tables/m5gpr28sp047j7w/links/c4olgvricf9nalu/records/{nocoid}", params={
            "limit": 1000
        }).json().get("list")

        member_ids = [str(item['Id']) for item in res]
        res = self._session.get(f"{self.base_url}/api/v2/tables/m3rsrrmnhhxxw0p/records", params={
            "limit": 1000,
            "where": f"(Id,in,{','.join(member_ids)})",
            "fields": "Telegram Username",
            "viewId": "vw72nyx0bmaak96s"
        })

        items = res.json().get("list")
        return [item['Telegram Username'] for item in items if item.get('Telegram Username')]

    def project_members(self, tag: str) -> list[str]:
        nocoid = self._session.get(f"{self.base_url}/api/v2/tables/ma3scczigje9u17/records", params={
            "limit": 1000,
            "where": f"(Tag,like,{tag})",
            "fields": "Id"
        }).json().get("list")[0].get('Id')

        res = self._session.get(f"{self.base_url}/api/v2/tables/ma3scczigje9u17/links/c96a46tetiedgvg/records/{nocoid}", params={
            "limit": 1000
        }).json().get("list")

        member_ids = [str(item['Id']) for item in res]
        res = self._session.get(f"{self.base_url}/api/v2/tables/m3rsrrmnhhxxw0p/records", params={
            "limit": 1000,
            "where": f"(Id,in,{','.join(member_ids)})",
            "fields": "Telegram Username",
            "viewId": "vw72nyx0bmaak96s"
        })

        items = res.json().get("list")
        return [item['Telegram Username'] for item in items if item.get('Telegram Username')]

    def role_members(self, tag: str) -> list[str]:
        nocoid = self._session.get(f"{self.base_url}/api/v2/tables/mpur65wgd6gqi98/records", params={
            "limit": 1000,
            "where": f"(Tag,like,{tag})",
            "fields": "Id"
        }).json().get("list")[0].get('Id')

        res = self._session.get(f"{self.base_url}/api/v2/tables/mpur65wgd6gqi98/links/cbuvnbm0wxwkfyo/records/{nocoid}", params={
            "limit": 1000
        }).json().get("list")

        member_ids = [str(item['Id']) for item in res]
        res = self._session.get(f"{self.base_url}/api/v2/tables/m3rsrrmnhhxxw0p/records", params={
            "limit": 1000,
            "where": f"(Id,in,{','.join(member_ids)})",
            "fields": "Telegram Username",
            "viewId": "vw72nyx0bmaak96s"
        })

        items = res.json().get("list")
        return [item['Telegram Username'] for item in items if item.get('Telegram Username')]

    def email_from_username(self, username: str) -> str:
        res = self._session.get(f"{self.base_url}/api/v2/tables/m3rsrrmnhhxxw0p/records", params={
            "limit": 1000,
            "where": f"(Telegram Username,like,@{username})~or(Telegram Username,like,{username})",
            "fields": "Team Email"
        })
        items = res.json().get("list")
        return items[0].get("Team Email", "") if items else None

    def username_from_email(self, email: str) -> str:
        res = self._session.get(f"{self.base_url}/api/v2/tables/m3rsrrmnhhxxw0p/records", params={
            "limit": 1000,
            "where": f"(Team Email,eq,{email})",
            "fields": "Telegram Username"
        })
        items = res.json().get("list")
        return items[0].get("Telegram Username", "") if items else None
