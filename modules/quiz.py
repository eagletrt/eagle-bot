import tomllib
import logging
import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# Load configuration from config.ini
with open(os.getenv("CONFIG_PATH"), "rb") as f:
    try:
        config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logging.error(f"modules/quiz - Error parsing data/config.ini: {e}")
        exit(1)

# Create a connection pool connected to the quiz PostgreSQL database.
connection_pool = pool.SimpleConnectionPool(
    1, 20,
    user=config['Database']['DB_USER'],
    password=os.getenv("DB_PASSWORD"),
    host=config['Database']['DB_HOST'],
    port=config['Database']['DB_PORT'],
    database=config['Database']['DB_QUIZ']
)

# Question types the bot can turn into a Telegram poll.
POLL_QUESTION_TYPES = ('single-choice', 'multi-choice')

@contextmanager
def get_connection():
    """Context manager to get and return connections from the pool."""
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)

def get_quiz(quiz_id):
    """Returns a dict with keys: quiz_id, year, class_, date, status, information, or None."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT quiz_id, year, class AS class_, date, status, information
                FROM quiz
                WHERE quiz_id = %s
            """, (quiz_id,))
            return cur.fetchone()

def get_all_quizzes():
    """Returns list of dicts ordered by quiz_id."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT quiz_id, year, class AS class_, date, status, information
                FROM quiz
                ORDER BY quiz_id
            """)
            return cur.fetchall()

def get_event(event_id):
    """Returns a dict with keys: event_id, short_name, event_name, country, website, or None."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT event_id, short_name, event_name, country, website
                FROM events
                WHERE event_id = %s
            """, (event_id,))
            return cur.fetchone()

def get_all_events():
    """Returns list of dicts ordered by event_id."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT event_id, short_name, event_name, country, website
                FROM events
                ORDER BY event_id
            """)
            return cur.fetchall()

def get_question(question_id, quiz_id):
    """
    Returns the question in the context of a quiz as a dict with keys:
    id, quiz_id, text, type, position_index, or None if the quiz does not contain it.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT q.question_id AS id, qq.quiz_id, q.text, q.type, qq.position_index
                FROM quiz_questions qq
                JOIN questions q USING (question_id)
                WHERE qq.question_id = %s AND qq.quiz_id = %s
            """, (question_id, quiz_id))
            return cur.fetchone()

def get_random_question(area_code=None):
    """
    Returns a dict (id, quiz_id, text, type, position_index) for a random
    single/multi-choice question, optionally filtered by area.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if area_code is not None:
                cur.execute("""
                    SELECT q.question_id AS id, qq.quiz_id, q.text, q.type, qq.position_index
                    FROM questions q
                    JOIN quiz_questions qq USING (question_id)
                    JOIN question_areas qa USING (question_id)
                    WHERE qa.area = %s AND q.type = ANY(%s::question_type[])
                    ORDER BY RANDOM()
                    LIMIT 1
                """, (area_code, list(POLL_QUESTION_TYPES)))
            else:
                cur.execute("""
                    SELECT q.question_id AS id, qq.quiz_id, q.text, q.type, qq.position_index
                    FROM questions q
                    JOIN quiz_questions qq USING (question_id)
                    WHERE q.type = ANY(%s::question_type[])
                    ORDER BY RANDOM()
                    LIMIT 1
                """, (list(POLL_QUESTION_TYPES),))
            return cur.fetchone()

def is_question_valid(question_id):
    """
    Validates the question based on its answers.
    A question is valid if it has:
        - Between 2 and 12 answers.
        - Exactly one correct answer.
        - All answer texts are 100 characters or less.
    """
    answers = get_question_answers(question_id)

    if not (2 <= len(answers) <= 12):
        return False

    correct_count = sum(1 for a in answers if a['is_correct'])
    if correct_count != 1:
        return False

    if not all(len(a['answer_text']) <= 100 for a in answers):
        return False

    return True

def get_question_answers(question_id):
    """Returns list of dicts with keys: answer_id, answer_text, is_correct, in display order."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT answer_id, answer_text, is_correct
                FROM answers
                WHERE question_id = %s
                ORDER BY answer_id
            """, (question_id,))
            return cur.fetchall()

def get_question_images(question_id):
    """
    Returns list of dicts with keys: img_id, filename, mime_type, data.
    `data` is the raw image as bytes; images whose download failed (NULL data) are skipped.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT i.img_id, i.filename, i.mime_type, i.data
                FROM question_images qi
                JOIN images i USING (img_id)
                WHERE qi.question_id = %s AND i.data IS NOT NULL
                ORDER BY i.img_id
            """, (question_id,))
            rows = cur.fetchall()
    # psycopg2 returns bytea as memoryview: convert so callers can pass it straight to Telegram.
    for row in rows:
        row['data'] = bytes(row['data'])
    return rows

def get_question_areas(question_id):
    """Returns list of area name strings."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT area
                FROM question_areas
                WHERE question_id = %s
                ORDER BY area
            """, (question_id,))
            return [row['area'] for row in cur.fetchall()]

def create_poll(poll_id, question_id, quiz_id, correct_option):
    """
    Inserts a poll mapping between Telegram poll ID and quiz question.
    (quiz_id, question_id) must exist in quiz_questions: pass the quiz the question was taken from.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO polls (poll_id, quiz_id, question_id, correct_option)
                VALUES (%s, %s, %s, %s)
            """, (str(poll_id), quiz_id, question_id, correct_option))
        conn.commit()
