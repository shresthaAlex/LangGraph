import sqlite3
from functools import partial

from agent import create_agent
from auth import register_user as auth_register_user, login_user as auth_login_user
from database import (
    init_db,
    increment_ai_count as db_increment_ai_count,
    store_conversation as db_store_conversation,
    load_conversation as db_load_conversation,
    retrieve_all_threads as db_retrieve_all_threads,
    store_conversation_name as db_store_conversation_name,
    delete_conversation as db_delete_conversation,
)

# ---------------- Database Setup ----------------
conn = sqlite3.connect('chatbot.db', check_same_thread=False)
init_db(conn)

# ---------------- Agent Setup ----------------
chatbot = create_agent(conn)

# ---------------- Auth Functions ----------------
register_user = partial(auth_register_user, conn)
login_user = partial(auth_login_user, conn)

# ---------------- Database Functions ----------------
increment_ai_count = partial(db_increment_ai_count, conn)
store_conversation = partial(db_store_conversation, conn)
load_conversation = partial(db_load_conversation, conn)
retrieve_all_threads = partial(db_retrieve_all_threads, conn)
store_conversation_name = partial(db_store_conversation_name, conn)
delete_conversation = partial(db_delete_conversation, conn)