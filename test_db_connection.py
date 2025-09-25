import psycopg2

PG_HOST = "localhost"
PG_DB = "devbot_db"
PG_USER = "devbot_user"
PG_PASS = "123456"

try:
    conn = psycopg2.connect(
        host=PG_HOST,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASS
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    db_version = cur.fetchone()
    print("PostgreSQL connection successful!")
    print(f"Database version: {db_version[0]}")
    cur.close()
    conn.close()
except Exception as e:
    print("Error connecting to PostgreSQL.")
    print(f"Error details: {e}")
