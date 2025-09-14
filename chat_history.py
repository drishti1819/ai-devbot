import psycopg2
from psycopg2 import sql
from datetime import datetime

DB_NAME = "devbot_db"
DB_USER = "devbot_user"
DB_PASSWORD = "123456"
DB_HOST = "localhost"
DB_PORT = "5432"

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)

def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL
                );
            """)
            conn.commit()

def save_chat(user_msg: str, bot_msg: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_history (user_message, bot_response)
                VALUES (%s, %s);
                """,
                (user_msg, bot_msg)
            )
            conn.commit()

def load_all_chats(limit=100):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT timestamp, user_message, bot_response
                FROM chat_history
                ORDER BY timestamp DESC
                LIMIT %s;
                """,
                (limit,)
            )
            return cur.fetchall()
