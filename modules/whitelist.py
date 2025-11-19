import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

class Whitelist:
    """ Manages user whitelisting based on tags from NocoDB. """
    
    def __init__(self, application):
        """ Initialize the Whitelist with tag cache and NocoDB client. """

        self.whitelist: dict[str, list[str]] = {}
        self.tag_cache = application.bot_data['tag_cache']
        self.nocodb = application.bot_data['nocodb']
        
        # run first cache update
        asyncio.create_task(self._update_cache())

        scheduler = AsyncIOScheduler()

        cron = application.bot_data['config']['Whitelist']['cron']

        scheduler.add_job(
            self._update_cache,
            'cron',
            **{field: value for field, value in zip(['minute', 'hour', 'day', 'month', 'day_of_week'], cron.split())}
        )

        scheduler.start()

        logging.info("modules/whitelist - Whitelist initialized and refresh scheduled with cron: " + cron)
        
    async def _update_cache(self) -> None:
        """ Update the whitelist cache from NocoDB. """

        tasks = []
        tag_map = []

        tag_types = {
            "areas": "area",
            "workgroups": "workgroup",
            "projects": "project",
            "roles": "role"
        }

        for tag_key, tag_type in tag_types.items():
            for tag in self.tag_cache.get(tag_key, []):
                tasks.append(self.nocodb.members(tag.lstrip("@"), tag_type))
                tag_map.append(tag)

        results = await asyncio.gather(*tasks)

        new_whitelist = dict(zip(tag_map, results))

        # Create @everyone by merging all members from all tags
        all_members = set()
        for member_list in new_whitelist.values():
            all_members.update(member_list)
        new_whitelist["@everyone"] = list(all_members)

        self.whitelist = new_whitelist

        logging.info("modules/whitelist - Whitelist cache updated from NocoDB.")

        return

    def is_user_whitelisted(self, username: str, tags: list[str]) -> bool:
        """ Check if a user is whitelisted for any of the provided tags. """

        # Put a @ before username to match tag format
        username = "@" + username

        # Check if the user is whitelisted for any of the provided tags
        for tag in tags:
            if tag == username:
                return True
            elif tag in self.whitelist and username in self.whitelist[tag]:
                return True
            
        return False

    def members_cache(self, tag: str) -> list[str]:
        """ Returns the cached members for a given tag and kind. """
        
        if tag in self.whitelist:
            return self.whitelist[tag]
        
        return []