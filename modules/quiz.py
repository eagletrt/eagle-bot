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
                SELECT quiz_id, year, class as class_, date, status, information
                FROM quiz
                WHERE quiz_id = %s
            """, (quiz_id,))
            return cur.fetchone()

def get_all_quizzes():
    """Returns list of dicts ordered by quiz_id."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT quiz_id, year, class as class_, date, status, information
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
    """Returns a dict with keys: id, quiz_id, text, type, position_index, or None."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, quiz as quiz_id, text, type, position_index
                FROM questions
                WHERE id = %s AND quiz = %s
            """, (question_id, quiz_id))
            return cur.fetchone()

def get_random_question(area_code=None):
    """Returns a dict for a random question (optionally filtered by area)."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if area_code is not None:
                cur.execute("""
                    SELECT q.id, q.quiz as quiz_id, q.text, q.type, q.position_index
                    FROM questions q
                    JOIN areas_questions aq ON q.id = aq.questions_id AND q.quiz = aq.questions_quiz
                    WHERE aq.areas = %s
                    ORDER BY RANDOM()
                    LIMIT 1
                """, (area_code,))
            else:
                cur.execute("""
                    SELECT id, quiz as quiz_id, text, type, position_index
                    FROM questions
                    ORDER BY RANDOM()
                    LIMIT 1
                """)
            return cur.fetchone()

def is_question_valid(question_id, quiz_id):
    """
    Validates the question based on its answers.
    A question is valid if it has:
        - Between 2 and 12 answers.
        - Exactly one correct answer.
        - All answer texts are 100 characters or less.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT answer_text, is_correct
                FROM answers
                WHERE question_id = %s AND question_quiz = %s
            """, (question_id, quiz_id))
            answers = cur.fetchall()

            if not (2 <= len(answers) <= 12):
                return False

            correct_count = sum(1 for a in answers if a['is_correct'])
            if correct_count != 1:
                return False

            if not all(len(a['answer_text']) <= 100 for a in answers):
                return False

            return True

def get_question_answers(question_id, quiz_id):
    """Returns list of dicts with keys: answer_id, answer_text, is_correct."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT answer_id, answer_text, is_correct
                FROM answers
                WHERE question_id = %s AND question_quiz = %s
            """, (question_id, quiz_id))
            return cur.fetchall()

def get_question_images(question_id, quiz_id):
    """Returns list of dicts with keys: id, path."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, path
                FROM images
                WHERE question_id = %s AND question_quiz = %s
            """, (question_id, quiz_id))
            return cur.fetchall()

def get_question_areas(question_id, quiz_id):
    """Returns list of area name strings."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT areas as name
                FROM areas_questions
                WHERE questions_id = %s AND questions_quiz = %s
            """, (question_id, quiz_id))
            return [row['name'] for row in cur.fetchall()]

def create_poll(poll_id, question_id, quiz_id, correct_option):
    """Inserts a poll mapping between Telegram poll ID and quiz question."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO polls (poll_id, question_id, question_quiz, correct_option)
                VALUES (%s, %s, %s, %s)
            """, (poll_id, question_id, quiz_id, correct_option))
        conn.commit()
