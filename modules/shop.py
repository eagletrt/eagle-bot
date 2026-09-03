import os
import tomllib
import logging
import random
from datetime import datetime
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager

with open(os.getenv("CONFIG_PATH"), "rb") as f:
    try:
        config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logging.error(f"modules/shop - Error parsing config: {e}")
        exit(1)

db_pool = SimpleConnectionPool(
    1, 20,
    user=config['Database']['DB_USER'],
    password=os.getenv("DB_PASSWORD"),
    host=config['Database']['DB_HOST'],
    port=config['Database']['DB_PORT'],
    database=config['Database']['DB_NAME']
)

@contextmanager
def get_connection():
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)

def create_tables():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS shop (
                    id SERIAL PRIMARY KEY,
                    chatid BIGINT NOT NULL,
                    threadid BIGINT
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS item (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    priority INT NOT NULL DEFAULT 0,
                    shop INT NOT NULL REFERENCES shop(id)
                )
            ''')
        conn.commit()

create_tables()

def get_or_create_shop(chat_id, thread_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if thread_id is not None:
                cur.execute('SELECT id FROM shop WHERE chatid = %s AND threadid = %s', (chat_id, thread_id))
            else:
                cur.execute('SELECT id FROM shop WHERE chatid = %s AND threadid IS NULL', (chat_id,))
            row = cur.fetchone()
            if row:
                return row[0]
            
            cur.execute('INSERT INTO shop (chatid, threadid) VALUES (%s, %s) RETURNING id', (chat_id, thread_id))
            shop_id = cur.fetchone()[0]
            conn.commit()
            return shop_id

def reset_shop(shop_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM item WHERE shop = %s', (shop_id,))
        conn.commit()

def remove_item(shop_id, item_idx):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM item WHERE shop = %s ORDER BY created_at LIMIT 1 OFFSET %s', (shop_id, item_idx))
            row = cur.fetchone()
            if row:
                cur.execute('DELETE FROM item WHERE id = %s', (row[0],))
                conn.commit()
                return True
            return False

def add_item(shop_id, text, created_by):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO item (text, created_by, created_at, priority, shop) VALUES (%s, %s, %s, 0, %s)', (text, created_by, datetime.now(), shop_id))
        conn.commit()

def format_shop(shop_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT text FROM item WHERE shop = %s ORDER BY created_at', (shop_id,))
            rows = cur.fetchall()
            
    if not rows:
        return "Shop list is empty."
        
    emojis = ['🪑', '📦', '🎁', '🧸', '🛍️', '📚', '🍀', '⚙️', '🚪', '🎨', '🔨', '🏎️', '🎹', '⚽️', '🎾', '✈️', '💻', '🖨️', '🕰️', '📻', '💾', '🧯', '📞', '💣', '🪓', '🪚', '🎸', '🪏', '🧱', '🪜', '🧽', '🪣', '⚰️', '🔩', '💸']
    
    items = []
    for (text,) in rows:
        emoji = random.choice(emojis)
        items.append(f"{emoji} {text}")
        
    return "\n\n".join(items)
