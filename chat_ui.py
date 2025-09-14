import streamlit as st
import psycopg2
from datetime import datetime
from auth import login_user  # updated login_user for @rathi.com
from chat import chat  # <-- import your backend AI chat function

# ---------- DB Config ----------
PG_HOST = "localhost"
PG_DB = "devbot_db"
PG_USER = "devbot_user"
PG_PASS = "123456"

# ---------- DB Helper ----------
def get_db():
    return psycopg2.connect(
        host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PASS
    )

# ---------- Chat History ----------
def get_chat_history(user_email):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                user_email TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

        cur.execute("""
            SELECT question, answer, timestamp
            FROM chat_history
            WHERE user_email = %s
            ORDER BY timestamp ASC
        """, (user_email,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        st.error(f"Error fetching chat history: {e}")
        return []

# ---------- Chat Saver ----------
def save_chat(user_email, question, answer):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO chat_history (user_email, question, answer)
            VALUES (%s, %s, %s)
        """, (user_email, question, answer))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Error saving chat: {e}")

# ---------- Streamlit Page Config ----------
st.set_page_config(page_title="DevBot", layout="wide")

# ---------- Session Init ----------
if "user" not in st.session_state:
    st.session_state["user"] = None

# ---------- Login ----------
if not st.session_state["user"]:
    st.title("DevBot Login")

    email = st.text_input("Enter your @rathi.com Email ID")
    if st.button("Login"):
        user, err = login_user(email)
        if user:
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error(err)

else:
    st.sidebar.write(f"Welcome {st.session_state['user']['email']}")
    if st.sidebar.button("Logout"):
        st.session_state["user"] = None
        st.rerun()

    st.title("DevBot Chat")

    # Display conversation history in chat style
    history = get_chat_history(st.session_state["user"]["email"])
    chat_container = st.container()
    with chat_container:
        for q, a, ts in history:
            st.markdown(f"**You ({ts.strftime('%H:%M:%S')}):** {q}")
            st.markdown(f"**Bot:** {a}")
            st.markdown("---")

    # Chat input box at bottom
    st.subheader("Ask a new question")
    user_input = st.text_input("Type your question:", key="chat_input")
    if st.button("Send"):
        if user_input.strip():
            try:
                # Call backend AI function
                bot_reply = chat(user_input)

                # Save Q&A in DB
                save_chat(st.session_state["user"]["email"], user_input, bot_reply)

                # Refresh UI to show updated conversation
                st.rerun()
            except Exception as e:
                st.error(f"Chat error: {e}")
        else:
            st.warning("Please type a question before sending.")

