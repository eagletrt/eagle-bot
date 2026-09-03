from datetime import datetime
import tomllib
import logging
import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager

# Load configuration from config.ini
with open(os.getenv("CONFIG_PATH"), "rb") as f:
    try:
        config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logging.error(f"modules/odg - Error parsing data/config.ini: {e}")
        exit(1)

# Create a connection pool at module level
connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,
    user=config['Database']['DB_USER'],
    password=os.getenv("DB_PASSWORD"),
    host=config['Database']['DB_HOST'],
    port=config['Database']['DB_PORT'],
    database=config['Database']['DB_NAME']
)

@contextmanager
def get_connection():
    """Context manager to get and return connections from the pool."""
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)

def create_tables():
    """Create odg and task tables if they don't exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS odg (
                    id SERIAL PRIMARY KEY,
                    chatid BIGINT NOT NULL,
                    threadid BIGINT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS task (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    priority INT NOT NULL DEFAULT 0,
                    odg INT NOT NULL REFERENCES odg(id)
                );
            """)
        conn.commit()

# Call create_tables() at module load
create_tables()

def get_or_create_odg(chat_id, thread_id):
    """Returns the odg row id, creating a new one if it doesn't exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            if thread_id is None:
                cur.execute("SELECT id FROM odg WHERE chatid = %s AND threadid IS NULL", (chat_id,))
            else:
                cur.execute("SELECT id FROM odg WHERE chatid = %s AND threadid = %s", (chat_id, thread_id))
            
            row = cur.fetchone()
            if row:
                return row[0]
            
            if thread_id is None:
                cur.execute("INSERT INTO odg (chatid, threadid) VALUES (%s, NULL) RETURNING id", (chat_id,))
            else:
                cur.execute("INSERT INTO odg (chatid, threadid) VALUES (%s, %s) RETURNING id", (chat_id, thread_id))
            
            odg_id = cur.fetchone()[0]
        conn.commit()
        return odg_id

def reset_odg(odg_id):
    """Deletes all tasks for this odg."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM task WHERE odg = %s", (odg_id,))
        conn.commit()

def remove_task(odg_id, task_idx):
    """Removes the task at offset task_idx (zero-based) ordered by created_at."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id FROM task 
                WHERE odg = %s 
                ORDER BY created_at 
                LIMIT 1 OFFSET %s
            """, (odg_id, task_idx))
            row = cur.fetchone()
            if row:
                cur.execute("DELETE FROM task WHERE id = %s", (row[0],))
                conn.commit()
                return True
            return False

def add_task(odg_id, text, created_by):
    """Inserts a new task."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO task (text, created_by, created_at, priority, odg)
                VALUES (%s, %s, %s, 0, %s)
            """, (text, created_by, datetime.now(), odg_id))
        conn.commit()

def format_odg(odg_id):
    """Returns the formatted string representation of the tasks."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT text, created_by FROM task
                WHERE odg = %s
                ORDER BY created_at
            """, (odg_id,))
            rows = cur.fetchall()
            
            if not rows:
                return "ODG list is empty."
            
            return "\n\n".join(f"📋 {text}\n👤 {created_by}" for text, created_by in rows)
