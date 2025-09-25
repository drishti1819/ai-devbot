import streamlit as st
import psycopg2
from datetime import datetime
from auth import login_user
from chat import chat # Re-importing the updated chat function
import tempfile
import os
from ingest_document import ingest_file
from config import PG_HOST, PG_DB, PG_USER, PG_PASS # Import PostgreSQL config

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
if "active_collections" not in st.session_state:
    st.session_state["active_collections"] = []

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

# ---------- Chat UI ----------
else:
    st.sidebar.write(f"Welcome {st.session_state['user']['email']}")
    if st.sidebar.button("Logout"):
        st.session_state["user"] = None
        st.session_state["active_collections"] = []
        st.rerun()

    # ---------- Document Upload ----------
    st.sidebar.subheader("Upload a Document for Context")
    uploaded_file = st.sidebar.file_uploader("Upload PDF/DOCX/TXT/MD", type=["pdf", "docx", "txt", "md"])
    if uploaded_file is not None:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            collection_name = ingest_file(tmp_path)
            if collection_name not in st.session_state["active_collections"]:
                st.session_state["active_collections"].append(collection_name)

            st.sidebar.success(f"Document '{uploaded_file.name}' ingested successfully.")
            os.unlink(tmp_path)
        except Exception as e:
            st.sidebar.error(f"Error ingesting document: {e}")

    st.title("DevBot Chat")

    history = get_chat_history(st.session_state["user"]["email"])
    chat_container = st.container()
    with chat_container:
        for q, a, ts in history:
            st.markdown(f"**You ({ts.strftime('%H:%M:%S')}):** {q}")
            st.markdown(f"**Bot:** {a}")
            st.markdown("---")

    st.subheader("Ask a new question")
    user_input = st.text_input("Type your question:", key="chat_input")

    if st.button("Send"):
        if user_input.strip():
            if not st.session_state["active_collections"]:
                st.warning("Please upload at least one document to provide context.")
            else:
                try:
                    bot_reply = chat(
                        user_input,
                        collection_names=st.session_state.get("active_collections")
                    )

                    save_chat(st.session_state["user"]["email"], user_input, bot_reply)

                    st.rerun()
                except Exception as e:
                    st.error(f"Chat error: {e}")
        else:
            st.warning("Please type a question before sending.")
