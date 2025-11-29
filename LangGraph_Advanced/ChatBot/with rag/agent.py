from typing import TypedDict, Annotated
from dotenv import load_dotenv
import requests
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool, BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio
import threading
import os
import tempfile
import aiosqlite
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS

# Import db functions
from database import add_document, get_document_for_thread

load_dotenv()

# Dedicated async loop for backend tasks
_ASYNC_LOOP = asyncio.new_event_loop()
_ASYNC_THREAD = threading.Thread(target=_ASYNC_LOOP.run_forever, daemon=True)
_ASYNC_THREAD.start()

def _submit_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, _ASYNC_LOOP)

def run_async(coro):
    return _submit_async(coro).result()

def submit_async_task(coro):
    """Schedule a coroutine on the backend event loop."""
    return _submit_async(coro)

# ---------------- LLM Setup ----------------
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


# ---------------- Vector Store ----------------
VECTORSTORE_DIR = "vectorstores"
if not os.path.exists(VECTORSTORE_DIR):
    os.makedirs(VECTORSTORE_DIR)

# ---------------- PDF Ingestion ----------------
async def ingest_pdf(conn: aiosqlite.Connection, file_bytes: bytes, thread_id: str, filename: str) -> dict:
    """
    Build a FAISS retriever for the uploaded PDF and store it for the thread.
    Returns a summary dict that can be surfaced in the UI.
    """
    if not file_bytes:
        raise ValueError("No bytes received for ingestion.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name

    try:
        loader = PyPDFLoader(temp_path)
        docs = await asyncio.to_thread(loader.load)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_documents(docs)

        vector_store = await asyncio.to_thread(FAISS.from_documents, chunks, embeddings)
        
        # Save the vector store
        vectorstore_path = os.path.join(VECTORSTORE_DIR, f"{thread_id}.faiss")
        await asyncio.to_thread(vector_store.save_local, vectorstore_path)

        doc_info = {
            "filename": filename,
            "documents": len(docs),
            "chunks": len(chunks),
        }

        # Store metadata in the database
        await add_document(conn, thread_id, filename, vectorstore_path, doc_info)
        
        return doc_info
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

# ---------------- Tools ----------------
search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    # ... (implementation remains the same)
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

@tool
async def rag_tool(query: str, thread_id: str = None) -> dict:
    """
    Retrieve relevant information from the uploaded PDF for this chat thread.
    Always include the thread_id when calling this tool.
    """
    if not thread_id:
        return {
            "error": f"rag_tool was called without a thread_id. Query: {query}",
            "query": query,
        }

    async with aiosqlite.connect(database="chatbot.db") as conn:
        doc_info = await get_document_for_thread(conn, thread_id)
    
    if doc_info is None:
        return {
            "error": f"No document indexed for this chat. (Thread ID: {thread_id}). Upload a PDF first.",
            "query": query,
        }
    
    vectorstore_path = os.path.join(VECTORSTORE_DIR, f"{thread_id}.faiss")
    if not os.path.exists(vectorstore_path):
        return {
            "error": f"Vector store not found for this thread. (Thread ID: {thread_id})",
            "query": query,
        }

    try:
        faiss_index = await asyncio.to_thread(
            FAISS.load_local,
            folder_path=vectorstore_path,
            embeddings=embeddings,
            allow_dangerous_deserialization=True
        )
        
        retriever = faiss_index.as_retriever(search_type="similarity", search_kwargs={"k": 4})
        result = await retriever.ainvoke(query)
        
        context = [doc.page_content for doc in result]
        metadata = [doc.metadata for doc in result]

        return {
            "query": query,
            "context": context,
            "metadata": metadata,
            "source_file": doc_info.get("filename"),
        }
    except Exception as e:
        return {"error": str(e), "query": query}


# --- MCP Client Setup ---
client = MultiServerMCPClient(
    {
        "expense": {
            "transport": "streamable_http",
            "url": "https://alexmcp.fastmcp.app/mcp"
        }
    }
)

def load_mcp_tools() -> list[BaseTool]:
    try:
        mcp_tools = run_async(client.get_tools())
        return mcp_tools
    except Exception as e:
        print(f"Failed to load MCP tools: {e}")
        return []

mcp_tools = load_mcp_tools()

tools = [search_tool, get_stock_price, calculator, rag_tool, *mcp_tools]
llm_with_tools = llm.bind_tools(tools) if tools else llm

# ---------------- Chat State ----------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# ---------------- Chat Node ----------------
async def chat_node(state: ChatState, config=None):
    """LLM node that may answer or request a tool call."""
    messages = state["messages"]
    
    response = await llm_with_tools.ainvoke(messages)

    if hasattr(response, "tool_calls") and response.tool_calls:
        thread_id = config.get("configurable", {}).get("thread_id")
        if thread_id:
            for call in response.tool_calls:
                if call.get('name') == 'rag_tool':
                    if call.get('args') is None:
                        call['args'] = {}
                    if 'thread_id' not in call['args'] or not call['args']['thread_id']:
                        call['args']['thread_id'] = thread_id
    
    return {"messages": [response]}

tool_node = ToolNode(tools) if tools else None

# ---------------- Agent Creation ----------------
def create_agent(conn):
    checkpointer = AsyncSqliteSaver(conn=conn)
    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_edge(START, "chat_node")

    if tool_node:
        graph.add_node("tools", tool_node)
        graph.add_conditional_edges("chat_node", tools_condition)
        graph.add_edge("tools", "chat_node")
    else:
        graph.add_edge("chat_node", END)

    return graph.compile(checkpointer=checkpointer)