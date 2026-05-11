import os
import logging
import psycopg2
from datetime import datetime

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

    def oreLab(self, email: str) -> dict:
        """ Call the ore lab endpoint for a given email. """

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:

                now = datetime.now()

                query = f"""
                    SELECT "entrata", "uscita" FROM "presenzalab"
                    WHERE "email" = '{email}' AND "entrata" >= '{now.year}-{now.month}-01' AND "uscita" IS NOT NULL
                    ORDER BY "entrata" DESC
                """

                cursor.execute(query)
                rows = cursor.fetchall()
                
                if not rows:
                    logging.warning(f"modules/inlab - No ore data found for user {email}")
                    return []
                
                result = sum([(row[1] - row[0]).total_seconds() / 3600 for row in rows])
                logging.info(f"modules/inlab - Retrieved ore data for user {email}: {result}")
                return result
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
