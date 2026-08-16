import psycopg2
import logging
import os

class DatabaseClient:
    """ Client for querying PostgreSQL database. """

    def __init__(self, application):
        """ Initialize PostgreSQL client with connection parameters. """

        self.dbconf = application.bot_data['config']['Database']

        self.connection_params = {
            'host': self.dbconf['DB_HOST'],
            'port': self.dbconf['DB_PORT'],
            'database': self.dbconf['DB_TEAM'],
            'user': self.dbconf['DB_USER'],
            'password': os.getenv("DB_PASSWORD")
        }

        logging.info("modules/database - Database client initialized")

    def _get_connection(self):
        """ Create and return a new database connection. """
        try:
            return psycopg2.connect(**self.connection_params)
        except psycopg2.Error as e:
            logging.error(f"modules/database - Database connection failed: {e}")
            raise

    async def load_tag_cache(self) -> dict[str, list[str]]:
        """ Load and return the tag cache for areas, workgroups, projects, and roles in a single query. """

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                query = f"""
                    SELECT 'areas' AS kind, "Tag" FROM {self.dbconf['bases']['hrBase']}."Areas"
                    WHERE "__nc_deleted" IS NULL
                    UNION ALL
                    SELECT 'workgroups' AS kind, "Tag" FROM {self.dbconf['bases']['hrBase']}."Projects"
                    WHERE "Type" = 'Workgroup' AND "__nc_deleted" IS NULL
                    UNION ALL
                    SELECT 'projects' AS kind, "Tag" FROM {self.dbconf['bases']['hrBase']}."Projects"
                    WHERE "Type" = 'Project' AND "__nc_deleted" IS NULL
                    UNION ALL
                    SELECT 'roles' AS kind, "Tag" FROM {self.dbconf['bases']['hrBase']}."Roles"
                    WHERE "__nc_deleted" IS NULL
                """

                cursor.execute(query)
                rows = cursor.fetchall()
                
                tag_cache = {
                    "areas": [],
                    "workgroups": [],
                    "projects": [],
                    "roles": ["@pm", "@rp"]
                }

                if not rows:
                    logging.warning("modules/database - No tags found.")
                    return tag_cache
                
                for row in rows:
                    kind = row[0]
                    tag = f"@{row[1].lower().strip()}"
                    tag_cache[kind].append(tag)
                
                for kind in tag_cache:
                    tag_cache[kind].sort()

                logging.info(f"modules/database - Retrieved {len(rows)} tags in total.")
                return tag_cache
        except Exception as e:
            logging.error(f"modules/database - Error loading tag cache: {e}")
            raise
        finally:
            conn.close()

    async def load_all_members(self) -> dict[str, list[str]]:
        """ Load all members for all tags (Areas, Projects, Workgroups, Roles) in a single query. """

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                query = f"""
                    SELECT a."Tag" as tag, p."Telegram_Username" FROM {self.dbconf['bases']['hrBase']}."People" p
                    JOIN {self.dbconf['bases']['hrBase']}."_nc_m2m_People_Areas" m ON p."id" = m."People_id"
                    JOIN {self.dbconf['bases']['hrBase']}."Areas" a ON m."Areas_id" = a."id"
                    WHERE (p."State" = 'Active Member' OR p."State" = 'In trial' OR p."State" = 'Reachable') AND a."__nc_deleted" IS NULL AND p."__nc_deleted" IS NULL
                    UNION ALL
                    SELECT pr."Tag" as tag, p."Telegram_Username" FROM {self.dbconf['bases']['hrBase']}."People" p
                    JOIN {self.dbconf['bases']['hrBase']}."_nc_m2m_People_Projects" m ON p."id" = m."People_id"
                    JOIN {self.dbconf['bases']['hrBase']}."Projects" pr ON m."Projects_id" = pr."id"
                    WHERE (p."State" = 'Active Member' OR p."State" = 'In trial' OR p."State" = 'Reachable') AND pr."__nc_deleted" IS NULL AND p."__nc_deleted" IS NULL
                    UNION ALL
                    SELECT r."Tag" as tag, p."Telegram_Username" FROM {self.dbconf['bases']['hrBase']}."People" p
                    JOIN {self.dbconf['bases']['hrBase']}."_nc_m2m_People_Roles" m ON p."id" = m."People_id"
                    JOIN {self.dbconf['bases']['hrBase']}."Roles" r ON m."Roles_id" = r."id"
                    WHERE (p."State" = 'Active Member' OR p."State" = 'In trial' OR p."State" = 'Reachable') AND r."__nc_deleted" IS NULL AND p."__nc_deleted" IS NULL
                    UNION ALL
                    SELECT 'pm' as tag, p."Telegram_Username" FROM {self.dbconf['bases']['hrBase']}."People" p
                    JOIN {self.dbconf['bases']['hrBase']}."_nc_m2m_People_Projects1" m ON p."id" = m."People_id"
                    JOIN {self.dbconf['bases']['hrBase']}."Projects" pr ON m."Projects_id" = pr."id"
                    WHERE pr."Type" = 'Project' AND (p."State" = 'Active Member' OR p."State" = 'In trial' OR p."State" = 'Reachable') AND pr."__nc_deleted" IS NULL AND p."__nc_deleted" IS NULL
                    UNION ALL
                    SELECT 'rp' as tag, p."Telegram_Username" FROM {self.dbconf['bases']['hrBase']}."People" p
                    JOIN {self.dbconf['bases']['hrBase']}."_nc_m2m_People_Projects1" m ON p."id" = m."People_id"
                    JOIN {self.dbconf['bases']['hrBase']}."Projects" pr ON m."Projects_id" = pr."id"
                    WHERE pr."Type" = 'Workgroup' AND (p."State" = 'Active Member' OR p."State" = 'In trial' OR p."State" = 'Reachable') AND pr."__nc_deleted" IS NULL AND p."__nc_deleted" IS NULL
                """

                cursor.execute(query)
                rows = cursor.fetchall()
                
                members_map = {}
                for row in rows:
                    if not row[0] or not row[1]:
                        continue
                    tag = f"@{row[0].lower().strip()}"
                    username = f"{row[1].lower().strip()}"
                    if tag not in members_map:
                        members_map[tag] = []
                    members_map[tag].append(username)
                
                logging.info(f"modules/database - Retrieved members for {len(members_map)} tags in a single query.")
                return members_map
        except Exception as e:
            logging.error(f"modules/database - Error loading all members: {e}")
            raise
        finally:
            conn.close()

    async def email_from_username(self, username: str) -> str:
        """ Lookup the Team Email for a given Telegram username. """

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                query = f"""
                    SELECT "University_Email" FROM {self.dbconf['bases']['hrBase']}."People"
                    WHERE "Telegram_Username" ILIKE %s AND "__nc_deleted" IS NULL
                    LIMIT 1
                """
                cursor.execute(query, (f"@{username}",))
                result = cursor.fetchone()
                
                if not result:
                    logging.warning(f"modules/database - No email found for username: @{username}")
                    return None

                logging.info(f"modules/database - Retrieved email for username @{username}")
                return result[0].replace("@studenti.unitn.it", "@eagletrt.it")
        except Exception as e:
            logging.error(f"modules/database - Error fetching email for username {username}: {e}")
            raise
        finally:
            conn.close()

    async def username_from_email(self, email: str) -> str:
        """ Lookup the Telegram Username for a given Team Email. """

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                query = f"""
                    SELECT "Telegram_Username" FROM {self.dbconf['bases']['hrBase']}."People"
                    WHERE "University_Email" = %s AND "__nc_deleted" IS NULL
                    LIMIT 1
                """

                email = email.replace("@eagletrt.it", "@studenti.unitn.it")
                cursor.execute(query, (email,))
                result = cursor.fetchone()
                
                if not result:
                    logging.warning(f"modules/database - No username found for email: {email}")
                    return None
                
                logging.info(f"modules/database - Retrieved username for email {email}")
                return result[0] if result else None
        except Exception as e:
            logging.error(f"modules/database - Error fetching username for email {email}: {e}")
            raise
        finally:
            conn.close()
