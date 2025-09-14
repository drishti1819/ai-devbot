# auth.py
import psycopg2

PG_HOST = "db"
PG_DB = "devbot_db"
PG_USER = "devbot_user"
PG_PASS = "devbot_pass"

def get_db():
    return psycopg2.connect(
        host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PASS
    )

# Domain-based "login" — no password, just email check
def login_user(email):
    email = email.strip().lower()
    if not email.endswith("@rathi.com"):
        return None, "Please use your official '@rathi.com' email address."

    # Optional: store or update the user in DB for tracking
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users (email, is_verified)
            VALUES (%s, TRUE)
            ON CONFLICT (email) DO UPDATE SET is_verified = TRUE
        """, (email,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        cur.close()
        conn.close()

    return {"email": email}, None
