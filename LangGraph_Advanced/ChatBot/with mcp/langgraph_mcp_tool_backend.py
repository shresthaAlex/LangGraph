import aiosqlite
from functools import partial
import asyncio

# Import async helpers from agent
from agent import create_agent, run_async, submit_async_task

# Import the new async auth and db functions
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

# ----------------- Unified Asynchronous Backend Setup -----------------
async def setup_backend():
    # A single aiosqlite connection for the entire application
    conn = await aiosqlite.connect(database="chatbot.db")
    
    # Initialize database schema
    await init_db(conn)
    
    # Create the async-compatible agent
    chatbot_agent = create_agent(conn)
    
    return chatbot_agent, conn

# Run async setup in the background loop to get the chatbot and connection
chatbot, conn = run_async(setup_backend())

# --- Create partial functions for all backend operations, binding the async connection ---

# Auth functions
register_user = partial(auth_register_user, conn)
login_user = partial(auth_login_user, conn)

# Database functions for UI state and user management
increment_ai_count = partial(db_increment_ai_count, conn)
store_conversation = partial(db_store_conversation, conn)
load_conversation_db = partial(db_load_conversation, conn) 
retrieve_all_threads_db = partial(db_retrieve_all_threads, conn)
store_conversation_name = partial(db_store_conversation_name, conn)
delete_conversation = partial(db_delete_conversation, conn)


# ----------------- Special function for interacting with the agent's internal state -----------------
async def load_conversation_from_checkpointer(thread_id: str):
    """
    Loads conversation history directly from the LangGraph async checkpointer.
    This reflects the agent's actual state.
    """
    state = await chatbot.aget_state(config={"configurable": {"thread_id": thread_id}})
    return state.values.get("messages", [])