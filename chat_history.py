import psycopg2
from psycopg2 import sql
import os # Add this missing import
from datetime import datetime

# Centralize DB Config
DB_NAME = "devbot_db"
DB_USER = "devbot_user"
DB_PASSWORD = "123456"
DB_HOST = "localhost"
DB_PORT = "5432"

DATABASE_URL = os.getenv("DATABASE_URL")

# Handle connection error
try:
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
    else:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
except Exception as e:
    print(f"Error connecting to PostgreSQL: {e}")
    conn = None

def get_connection():
    if conn and not conn.closed:
        return conn
    else:
        try:
            return psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
        except Exception as e:
            print(f"Error establishing new PostgreSQL connection: {e}")
            return None

def init_db():
    connection = get_connection()
    if connection is None:
        return
    
    with connection as conn:
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
    connection = get_connection()
    if connection is None:
        return
    
    with connection as conn:
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
    connection = get_connection()
    if connection is None:
        return []

    with connection as conn:
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
