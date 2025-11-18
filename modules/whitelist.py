import logging

class Whitelist:
    """ Manages user whitelisting based on tags from NocoDB. """
    
    def __init__(self, tag_cache: dict[str, list[str]], nocodb):
        """ Initialize the Whitelist with tag cache and NocoDB client. """

        self.whitelist: dict[str, list[str]] = {}
        self.tag_cache = tag_cache
        self.nocodb = nocodb
        self._update_cache()

        logging.info("modules/whitelist - Whitelist initialized and cache populated.")
        
    def _update_cache(self) -> None:
        """ Update the whitelist cache from NocoDB. """

        for area in self.tag_cache.get("areas", []):
            self.whitelist[area] = self.nocodb.members(area.lstrip("@"), 'area')
        for workgroup in self.tag_cache.get("workgroups", []):
            self.whitelist[workgroup] = self.nocodb.members(workgroup.lstrip("@"), 'workgroup')
        for project in self.tag_cache.get("projects", []):
            self.whitelist[project] = self.nocodb.members(project.lstrip("@"), 'project')
        for role in self.tag_cache.get("roles", []):
            self.whitelist[role] = self.nocodb.members(role.lstrip("@"), 'role')

        # Create @everyone by merging all members from all tags
        all_members = set()
        for member_list in self.whitelist.values():
            all_members.update(member_list)
        self.whitelist["@everyone"] = list(all_members)

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
            
        # Refresh cache and recheck
        self._update_cache()
        for tag in tags:
            if tag in self.whitelist and username in self.whitelist[tag]:
                return True
            
        return False
