import os
import logging
import psycopg2
from datetime import datetime, timedelta

class InLabClient:
    """ Client for interacting with the inlab database. """

    def __init__(self, application):
        """ Initialize PostgreSQL client with connection parameters. """

        self.dbconf = application.bot_data['config']['Database']

        self.connection_params = {
            'host': self.dbconf['DB_HOST'],
            'port': self.dbconf['DB_PORT'],
            'database': self.dbconf['DB_API'],
            'user': self.dbconf['DB_USER'],
            'password': os.getenv("DB_PASSWORD")
        }

        logging.info("modules/inlab - Database client initialized")

    def _get_connection(self):
        """ Create and return a new database connection. """
        try:
            return psycopg2.connect(**self.connection_params)
        except psycopg2.Error as e:
            logging.error(f"modules/inlab - Database connection failed: {e}")
            raise

    def oreLab(self, email: str) -> float:
        """ Call the ore lab endpoint for a given email. """

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:

                now = datetime.now()
                month_start = f"{now.year}-{now.month:02d}-01"

                query = """
                    SELECT "entrata", "uscita" FROM "presenzalab"
                    WHERE "email" = %s AND "entrata" >= %s AND "isvalid" = TRUE
                    ORDER BY "entrata" DESC
                """

                cursor.execute(query, (email, month_start))
                rows = cursor.fetchall()
                
                if not rows:
                    logging.warning(f"modules/inlab - No ore data found for user {email}")
                    return 0.0
                
                result = sum([((row[1] or datetime.now()) - row[0]).total_seconds() / 3600 for row in rows])
                logging.info(f"modules/inlab - Retrieved ore data for user {email}: {result}")
                return result
        except Exception as e:
            logging.error(f"modules/inlab - Error fetching ore data for user {email}: {e}")
            raise
        finally:
            conn.close()

    def oreLabWeek(self, email: str) -> dict:
        """Call the ore lab week endpoint for a given email.

        Returns a dict with hours summed per weekday (Monday..Sunday).
        """

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:

                now = datetime.now()
                week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")

                query = """
                    SELECT "entrata", "uscita" FROM "presenzalab"
                    WHERE "email" = %s AND "entrata" >= %s AND "isvalid" = TRUE
                    ORDER BY "entrata" DESC
                """

                cursor.execute(query, (email, week_start))
                rows = cursor.fetchall()
                
                if not rows:
                    logging.warning(f"modules/inlab - No ore data found for user {email} this week")
                    return {}

                # Initialize weekdays Monday(0) .. Sunday(6)
                weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                per_day = {d: 0.0 for d in weekdays}

                for entrata, uscita in rows:
                    end = uscita or datetime.now()
                    hours = (end - entrata).total_seconds() / 3600
                    day = entrata.weekday()
                    per_day[weekdays[day]] += hours

                logging.info(f"modules/inlab - Retrieved ore per-day data for user {email} this week: {per_day}")
                return per_day
        except Exception as e:
            logging.error(f"modules/inlab - Error fetching ore data for user {email} this week: {e}")
            raise
        finally:
            conn.close()

    def oreLabMonth(self, email: str) -> dict:
        """Call the ore lab month endpoint for a given email.

        Returns a dict with hours summed per day of the month (1..31).
        """
        
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:

                now = datetime.now()
                month_start = now.replace(day=1).strftime("%Y-%m-%d")

                query = """
                    SELECT "entrata", "uscita" FROM "presenzalab"
                    WHERE "email" = %s AND "entrata" >= %s AND "isvalid" = TRUE
                    ORDER BY "entrata" DESC
                """

                cursor.execute(query, (email, month_start))
                rows = cursor.fetchall()
                
                if not rows:
                    logging.warning(f"modules/inlab - No ore data found for user {email} this month")
                    return {}

                # Initialize days of the month (1..31)
                per_day = {d: 0.0 for d in range(1, 32)}

                for entrata, uscita in rows:
                    end = uscita or datetime.now()
                    hours = (end - entrata).total_seconds() / 3600
                    day = entrata.day
                    per_day[day] += hours

                logging.info(f"modules/inlab - Retrieved ore per-day data for user {email} this month: {per_day}")
                return per_day
        except Exception as e:
            logging.error(f"modules/inlab - Error fetching ore data for user {email} this month: {e}")
            raise
        finally:
            conn.close()

    def oreLabYear(self, email: str) -> dict:
        """ Call the ore lab year endpoint for a given email. 
        
        Returns a dict with hours summed per month (January..December).
        """

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:

                now = datetime.now()
                year_start = f"{now.year}-01-01"

                query = """
                    SELECT "entrata", "uscita" FROM "presenzalab"
                    WHERE "email" = %s AND "entrata" >= %s AND "isvalid" = TRUE
                    ORDER BY "entrata" DESC
                """

                cursor.execute(query, (email, year_start))
                rows = cursor.fetchall()
                
                if not rows:
                    logging.warning(f"modules/inlab - No ore data found for user {email} this year")
                    return {}

                # Initialize months January(1) .. December(12)
                months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                per_month = {m: 0.0 for m in months}

                for entrata, uscita in rows:
                    end = uscita or datetime.now()
                    hours = (end - entrata).total_seconds() / 3600
                    month = entrata.month
                    per_month[months[month - 1]] += hours

                logging.info(f"modules/inlab - Retrieved ore per-month data for user {email} this year: {per_month}")
                return per_month
        except Exception as e:
            logging.error(f"modules/inlab - Error fetching ore data for user {email} this year: {e}")
            raise
        finally:
            conn.close()

    def oreLabSeason(self, email: str) -> dict:
        """ Call the ore lab season endpoint for a given email. 
        
        Returns a dict with hours summed per season (starting from september).
        """

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:

                query = """
                    SELECT "entrata", "uscita" FROM "presenzalab"
                    WHERE "email" = %s AND "isvalid" = TRUE
                    ORDER BY "entrata" DESC
                """

                cursor.execute(query, (email,))
                rows = cursor.fetchall()
                
                if not rows:
                    logging.warning(f"modules/inlab - No ore data found for user {email} this season")
                    return {}

                seasons = ['Fenice | 2021-2022', 'Fenice EVO | 2022-2023', 'Hydra | 2023-2024', 'Kraken | 2024-2025', 'Kraken | 2025-2026']

                per_season = {s: 0.0 for s in seasons}
                for entrata, uscita in rows:
                    end = uscita or datetime.now()
                    hours = (end - entrata).total_seconds() / 3600
                    year = entrata.year
                    month = entrata.month

                    if month >= 9:
                        season_key = f"{year}-{year + 1}"
                    else:
                        season_key = f"{year - 1}-{year}"

                    if season_key == "2021-2022":
                        per_season['Fenice | 2021-2022'] += hours
                    elif season_key == "2022-2023":
                        per_season['Fenice EVO | 2022-2023'] += hours
                    elif season_key == "2023-2024":
                        per_season['Hydra | 2023-2024'] += hours
                    elif season_key == "2024-2025":
                        per_season['Kraken | 2024-2025'] += hours
                    elif season_key == "2025-2026":
                        per_season['Kraken | 2025-2026'] += hours

                logging.info(f"modules/inlab - Retrieved ore per-season data for user {email} this season: {per_season}")
                return per_season
        except Exception as e:
            logging.error(f"modules/inlab - Error fetching ore data for user {email} this season: {e}")
            raise
        finally:
            conn.close()

    def oreLabTotal(self, email: str) -> float:
        """ Call the ore lab total endpoint for a given email. 
        
        Returns the total hours spent in the lab for the user.
        """

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:

                query = """
                    SELECT SUM("uscita" - "entrata") FROM "presenzalab"
                    WHERE "email" = %s AND "isvalid" = TRUE
                    ORDER BY "entrata" DESC
                """

                cursor.execute(query, (email,))
                result = cursor.fetchone()[0]

                if not result:
                    logging.warning(f"modules/inlab - No ore data found for user {email}")
                    return 0.0

                total_hours = result.total_seconds() / 3600
                logging.info(f"modules/inlab - Retrieved total ore data for user {email}: {total_hours}")
                return total_hours
        except Exception as e:
            logging.error(f"modules/inlab - Error fetching ore data for user {email}: {e}")
            raise
        finally:
            conn.close()

    def inlab(self) -> dict:
        """ Call the inlab endpoint. """

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:

                query = f"""
                    SELECT "email" FROM "presenzalab"
                    WHERE "uscita" IS NULL
                    ORDER BY "email"
                """

                cursor.execute(query)
                rows = cursor.fetchall()
                
                if not rows:
                    logging.warning(f"modules/inlab - No active lab members found")
                    return []
                
                result = [f"{row[0].lower().strip()}" for row in rows]
                logging.info(f"modules/inlab - Retrieved {len(result)} active lab members")
                return result
        except Exception as e:
            logging.error(f"modules/inlab - Error fetching active lab members: {e}")
            raise
        finally:
            conn.close()
