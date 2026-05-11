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

    def _get_connection(self):
        """ Create and return a new database connection. """
        return psycopg2.connect(**self.connection_params)

    async def tags(self, kind: str) -> list[str]:
        """ Return all tags for the given kind. """

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:

                if kind == "Area":
                    query = f"""
                        SELECT "Tag" FROM {self.dbconf['bases']['hrBase']}."Areas"
                        ORDER BY "Tag"
                    """
                elif kind == "Workgroup" or kind == "Project":
                    query = f"""
                        SELECT "Tag" FROM {self.dbconf['bases']['hrBase']}."Projects"
                        WHERE "Type" = '{kind}'
                        ORDER BY "Tag"
                    """
                elif kind == "Role":
                    query = f"""
                        SELECT "Tag" FROM {self.dbconf['bases']['hrBase']}."Roles"
                        ORDER BY "Tag"
                    """

                cursor.execute(query)
                rows = cursor.fetchall()
                
                if not rows:
                    return []
                
                # Format tags with @ prefix and lowercase
                return [f"@{row[0].lower().strip()}" for row in rows]
        finally:
            conn.close()

    async def members(self, tag: str, kind: str) -> list[str]:
        """ Return Telegram usernames for the given tag. """

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                
                if kind == "Area":
                    query = f"""
                        SELECT p."Telegram_Username" FROM {self.dbconf['bases']['hrBase']}."People" p
                        JOIN {self.dbconf['bases']['hrBase']}."_nc_m2m_People_Areas" m ON p."id" = m."People_id"
                        JOIN {self.dbconf['bases']['hrBase']}."Areas" a ON m."Areas_id" = a."id"
                        WHERE a."Tag" ILIKE %s AND (p."State" = 'Active Member' OR p."State" = 'In trial' OR p."State" = 'Reachable')
                        ORDER BY p."Telegram_Username"
                    """
                elif kind == "Workgroup" or kind == "Project":
                    query = f"""
                        SELECT p."Telegram_Username" FROM {self.dbconf['bases']['hrBase']}."People" p
                        JOIN {self.dbconf['bases']['hrBase']}."_nc_m2m_People_Projects" m ON p."id" = m."People_id"
                        JOIN {self.dbconf['bases']['hrBase']}."Projects" pr ON m."Projects_id" = pr."id"
                        WHERE pr."Tag" ILIKE %s AND (p."State" = 'Active Member' OR p."State" = 'In trial' OR p."State" = 'Reachable')
                        ORDER BY p."Telegram_Username"
                    """
                elif kind == "Role":
                    query = f"""
                        SELECT p."Telegram_Username" FROM {self.dbconf['bases']['hrBase']}."People" p
                        JOIN {self.dbconf['bases']['hrBase']}."_nc_m2m_People_Roles" m ON p."id" = m."People_id"
                        JOIN {self.dbconf['bases']['hrBase']}."Roles" r ON m."Roles_id" = r."id"
                        WHERE r."Tag" ILIKE %s AND (p."State" = 'Active Member' OR p."State" = 'In trial' OR p."State" = 'Reachable')
                        ORDER BY p."Telegram_Username"
                    """

                cursor.execute(query, (tag.upper(),))
                rows = cursor.fetchall()
                
                if not rows:
                    return []
                
                return [f"{row[0].lower().strip()}" for row in rows if row[0]]
        finally:
            conn.close()

    async def email_from_username(self, username: str) -> str:
        """ Lookup the Team Email for a given Telegram username. """

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                query = f"""
                    SELECT "University_Email" FROM {self.dbconf['bases']['hrBase']}."People"
                    WHERE "Telegram_Username" ILIKE %s
                    LIMIT 1
                """
                cursor.execute(query, (f"@{username}",))
                result = cursor.fetchone()
                
                return result[0].replace("@studenti.unitn.it", "@eagletrt.it")
        finally:
            conn.close()

    async def username_from_email(self, email: str) -> str:
        """ Lookup the Telegram Username for a given Team Email. """

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                query = f"""
                    SELECT "Telegram_Username" FROM {self.dbconf['bases']['hrBase']}."People"
                    WHERE "University_Email" = %s
                    LIMIT 1
                """

                email = email.replace("@eagletrt.it", "@studenti.unitn.it")
                cursor.execute(query, (email,))
                result = cursor.fetchone()
                
                return result[0] if result else None
        finally:
            conn.close()
