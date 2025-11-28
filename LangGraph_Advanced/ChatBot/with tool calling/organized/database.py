import sqlite3
import json

def init_db(conn: sqlite3.Connection):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        ai_count INTEGER DEFAULT 0,
        last_reset DATE
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        thread_id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        conversation_name TEXT NOT NULL,
        messages TEXT
    )
    ''')
    conn.commit()

def increment_ai_count(conn: sqlite3.Connection, username: str) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT ai_count FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    if row:
        ai_count = row[0] + 1
        cursor.execute("UPDATE users SET ai_count=? WHERE username=?", (ai_count, username))
        conn.commit()
        return ai_count
    return 0

def store_conversation(conn: sqlite3.Connection, thread_id, username, messages, conversation_name):
    cursor = conn.cursor()
    messages_json = json.dumps(messages)
    cursor.execute('''
        INSERT OR REPLACE INTO conversations (thread_id, username, conversation_name, messages)
        VALUES (?, ?, ?, ?)
    ''', (str(thread_id), username, conversation_name, messages_json))
    conn.commit()

def load_conversation(conn: sqlite3.Connection, thread_id, username):
    cursor = conn.cursor()
    cursor.execute("SELECT messages FROM conversations WHERE thread_id=? AND username=?", (thread_id, username))
    row = cursor.fetchone()
    return json.loads(row[0]) if row and row[0] else []

def retrieve_all_threads(conn: sqlite3.Connection, username):
    cursor = conn.cursor()
    cursor.execute("SELECT thread_id, conversation_name FROM conversations WHERE username=? ORDER BY rowid", (username,))
    rows = cursor.fetchall()
    chat_threads = [row[0] for row in rows]
    thread_names = {row[0]: row[1] for row in rows}
    return chat_threads, thread_names

def store_conversation_name(conn: sqlite3.Connection, thread_id, username, new_name):
    cursor = conn.cursor()
    cursor.execute("UPDATE conversations SET conversation_name=? WHERE thread_id=? AND username=?",
                   (new_name, str(thread_id), username))
    conn.commit()

def delete_conversation(conn: sqlite3.Connection, thread_id, username):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations WHERE thread_id=? AND username=?", (str(thread_id), username))
    conn.commit()
