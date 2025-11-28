import sqlite3
import json
from datetime import date
from typing import TypedDict, Annotated
from dotenv import load_dotenv
import bcrypt
import requests
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

load_dotenv()

# ---------------- LLM Setup ----------------
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

# ---------------- Tools ----------------
search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=8S6VBWTFZH9U6HDA"
    r = requests.get(url)
    return r.json()

tools = [search_tool, get_stock_price, calculator]
llm_with_tools = llm.bind_tools(tools)

# ---------------- Chat State ----------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# ---------------- Chat Node ----------------
def chat_node(state: ChatState):
    """LLM node that may answer or request a tool call."""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)

# ---------------- Database Setup ----------------
conn = sqlite3.connect('chatbot.db', check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# Ensure tables exist
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

# ---------------- Auth Utilities ----------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def register_user(username: str, password: str) -> dict:
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        return {"success": False, "error": "Username already exists"}
    
    cursor.execute(
        "INSERT INTO users (username, password_hash, ai_count, last_reset) VALUES (?, ?, 0, ?)",
        (username, hash_password(password), date.today())
    )
    conn.commit()
    return {"success": True}

def login_user(username: str, password: str) -> dict:
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, ai_count, last_reset FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    if not row:
        return {"success": False, "error": "Username does not exist"}

    password_hash, ai_count, last_reset = row
    if not check_password(password, password_hash):
        return {"success": False, "error": "Incorrect password"}

    # Reset daily AI counter if new day
    if last_reset != str(date.today()):
        ai_count = 0
        cursor.execute("UPDATE users SET ai_count=0, last_reset=? WHERE username=?", (date.today(), username))
        conn.commit()

    return {"success": True, "username": username, "ai_count": ai_count}

def increment_ai_count(username: str) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT ai_count FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    if row:
        ai_count = row[0] + 1
        cursor.execute("UPDATE users SET ai_count=? WHERE username=?", (ai_count, username))
        conn.commit()
        return ai_count
    return 0

# ---------------- Conversation Utilities ----------------
def store_conversation(thread_id, username, messages, conversation_name):
    cursor = conn.cursor()
    messages_json = json.dumps(messages)
    cursor.execute('''
        INSERT OR REPLACE INTO conversations (thread_id, username, conversation_name, messages)
        VALUES (?, ?, ?, ?)
    ''', (str(thread_id), username, conversation_name, messages_json))
    conn.commit()

def load_conversation(thread_id, username):
    cursor = conn.cursor()
    cursor.execute("SELECT messages FROM conversations WHERE thread_id=? AND username=?", (thread_id, username))
    row = cursor.fetchone()
    return json.loads(row[0]) if row and row[0] else []

def retrieve_all_threads(username):
    cursor = conn.cursor()
    cursor.execute("SELECT thread_id, conversation_name FROM conversations WHERE username=? ORDER BY rowid", (username,))
    rows = cursor.fetchall()
    chat_threads = [row[0] for row in rows]
    thread_names = {row[0]: row[1] for row in rows}
    return chat_threads, thread_names

def store_conversation_name(thread_id, username, new_name):
    cursor = conn.cursor()
    cursor.execute("UPDATE conversations SET conversation_name=? WHERE thread_id=? AND username=?",
                   (new_name, str(thread_id), username))
    conn.commit()

def delete_conversation(thread_id, username):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations WHERE thread_id=? AND username=?", (str(thread_id), username))
    conn.commit()

# ---------------- Graph Setup ----------------
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge('tools', 'chat_node')

chatbot = graph.compile(checkpointer=checkpointer)
