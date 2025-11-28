import aiosqlite
import json

async def init_db(conn: aiosqlite.Connection):
    await conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        ai_count INTEGER DEFAULT 0,
        last_reset DATE
    )
    ''')

    await conn.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        thread_id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        conversation_name TEXT NOT NULL,
        messages TEXT
    )
    ''')
    await conn.commit()

async def increment_ai_count(conn: aiosqlite.Connection, username: str) -> int:
    async with conn.execute("SELECT ai_count FROM users WHERE username=?", (username,)) as cursor:
        row = await cursor.fetchone()
    
    if row:
        ai_count = row[0] + 1
        await conn.execute("UPDATE users SET ai_count=? WHERE username=?", (ai_count, username))
        await conn.commit()
        return ai_count
    return 0

async def store_conversation(conn: aiosqlite.Connection, thread_id, username, messages, conversation_name):
    messages_json = json.dumps(messages)
    await conn.execute('''
        INSERT OR REPLACE INTO conversations (thread_id, username, conversation_name, messages)
        VALUES (?, ?, ?, ?)
    ''', (str(thread_id), username, conversation_name, messages_json))
    await conn.commit()

async def load_conversation(conn: aiosqlite.Connection, thread_id, username):
    async with conn.execute("SELECT messages FROM conversations WHERE thread_id=? AND username=?", (thread_id, username)) as cursor:
        row = await cursor.fetchone()
    return json.loads(row[0]) if row and row[0] else []

async def retrieve_all_threads(conn: aiosqlite.Connection, username):
    async with conn.execute("SELECT thread_id, conversation_name FROM conversations WHERE username=? ORDER BY rowid", (username,)) as cursor:
        rows = await cursor.fetchall()
    
    chat_threads = [row[0] for row in rows]
    thread_names = {row[0]: row[1] for row in rows}
    return chat_threads, thread_names

async def store_conversation_name(conn: aiosqlite.Connection, thread_id, username, new_name):
    await conn.execute("UPDATE conversations SET conversation_name=? WHERE thread_id=? AND username=?",
                   (new_name, str(thread_id), username))
    await conn.commit()

async def delete_conversation(conn: aiosqlite.Connection, thread_id, username):
    await conn.execute("DELETE FROM conversations WHERE thread_id=? AND username=?", (str(thread_id), username))
    await conn.commit()
