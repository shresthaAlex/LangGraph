import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
import queue
import uuid
import asyncio
import os
import shutil

from langgraph_mcp_tool_backend import (
    chatbot,
    load_conversation_from_checkpointer, # Load from agent state
    store_conversation,
    retrieve_all_threads_db,
    store_conversation_name,
    register_user,
    login_user,
    increment_ai_count,
    delete_conversation,
    run_async,
    submit_async_task,
    add_document, # New: Add document info to DB
    get_document_for_thread, # New: Get document info from DB
    ingest_pdf, # New: PDF ingestion function
)
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AIMessageChunk
from agent import VECTORSTORE_DIR # Import the directory where vectorstores are saved

MAX_AI_SEARCHES = 100

# ---------------- Cookie Setup ----------------
cookies = EncryptedCookieManager(
    prefix="langgraph_", password="7b9561efc4a6acf95c78285418225434533f70dd609026c8ff9ba1c50a5be6c6"
)
if not cookies.ready():
    st.stop()

# ---------------- Thread & Session Functions ----------------
def generate_thread_id():
    return str(uuid.uuid4())

# This function now only creates the new chat in the DB and sets the active thread_id.
# It no longer manipulates the session state lists directly.
async def create_new_chat_in_db(username: str):
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    st.session_state['message_history'] = []
    
    # Determine a default name and immediately add it to the session state
    default_name = "New Conversation" 
    st.session_state.setdefault('thread_names', {})[str(thread_id)] = default_name

    # Store the new, empty conversation in the database
    await store_conversation(thread_id, username, [], default_name)
    # Clear any document info for the new thread in session state
    st.session_state['current_doc_info'] = None


# Utility to convert LangChain messages to Streamlit format
def format_messages(messages):
    formatted = []
    if messages:
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, ToolMessage): # Do not display ToolMessage in chat history
                continue
            else:
                continue
            formatted.append({"role": role, "content": msg.content})
    return formatted

# ---------------- Session Defaults ----------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []
if 'thread_names' not in st.session_state:
    st.session_state['thread_names'] = {}
if 'ai_counter' not in st.session_state:
    st.session_state['ai_counter'] = 0
if 'current_doc_info' not in st.session_state:
    st.session_state['current_doc_info'] = None

# ---------------- Restore from Cookie ----------------
if cookies.get("username") and cookies.get("logged_in") == "True" and not st.session_state.get('logged_in'):
    st.session_state['logged_in'] = True
    st.session_state['username'] = cookies.get("username")
    st.session_state['ai_counter'] = int(cookies.get("ai_counter", 0))
    
    threads, names = run_async(retrieve_all_threads_db(st.session_state['username']))
    st.session_state['chat_threads'], st.session_state['thread_names'] = threads, names

    if st.session_state['chat_threads']:
        st.session_state['thread_id'] = st.session_state['chat_threads'][-1]
        messages = run_async(load_conversation_from_checkpointer(str(st.session_state['thread_id'])))
        st.session_state['message_history'] = format_messages(messages)
        st.session_state['current_doc_info'] = run_async(get_document_for_thread(str(st.session_state['thread_id'])))
    else:
        run_async(create_new_chat_in_db(st.session_state['username']))
        # Immediately refetch to populate the lists
        threads, names = run_async(retrieve_all_threads_db(st.session_state['username']))
        st.session_state['chat_threads'], st.session_state['thread_names'] = threads, names

    st.rerun()


# ---------------- Logout ----------------
def logout():
    st.session_state.clear()
    cookies["username"] = ""
    cookies["logged_in"] = "False"
    cookies["ai_counter"] = "0"
    cookies.save()
    st.session_state['logged_in'] = False
    
    # Clean up vectorstore directory if it exists
    if os.path.exists(VECTORSTORE_DIR):
        try:
            shutil.rmtree(VECTORSTORE_DIR)
            print(f"Cleaned up {VECTORSTORE_DIR} on logout.")
        except Exception as e:
            print(f"Error cleaning up {VECTORSTORE_DIR}: {e}")

    st.rerun()

# ---------------- Login/Register ----------------
if not st.session_state.get('logged_in'):
    st.markdown("<h1 style='text-align: center;'> Welcome to <span style='color:#2563eb;'>LangGraph </span></h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        st.subheader("🌟 Login to continue")
        username_login = st.text_input("Username", key="login_user")
        password_login = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            res = run_async(login_user(username_login, password_login))
            if res["success"]:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username_login
                st.session_state['ai_counter'] = res.get("ai_count", 0)
                
                threads, names = run_async(retrieve_all_threads_db(username_login))
                st.session_state['chat_threads'], st.session_state['thread_names'] = threads, names

                if st.session_state['chat_threads']:
                    st.session_state['thread_id'] = st.session_state['chat_threads'][-1]
                    messages = run_async(load_conversation_from_checkpointer(str(st.session_state['thread_id'])))
                    st.session_state['message_history'] = format_messages(messages)
                    st.session_state['current_doc_info'] = run_async(get_document_for_thread(str(st.session_state['thread_id'])))
                else:
                    run_async(create_new_chat_in_db(username_login))
                    threads, names = run_async(retrieve_all_threads_db(username_login))
                    st.session_state['chat_threads'], st.session_state['thread_names'] = threads, names

                cookies["username"] = username_login
                cookies["logged_in"] = "True"
                cookies["ai_counter"] = str(st.session_state['ai_counter'])
                cookies.save()
                st.rerun()
            else:
                st.error(res["error"])
    with tab2:
        st.subheader("🆕 Create a new account")
        username_reg = st.text_input("Choose username", key="reg_user")
        password_reg = st.text_input("Choose password", type="password", key="reg_pass")
        if st.button("Register"):
            res = run_async(register_user(username_reg.strip(), password_reg.strip()))
            if res["success"]:
                st.success(f"User {username_reg} registered successfully!")
            else:
                st.error(res["error"])
    st.stop()


# ---------------- Sidebar ----------------
st.sidebar.title('🤖 LangGraph Chatbot')
st.sidebar.button("🔒 Logout", on_click=logout)
st.sidebar.markdown("# 💬 My Conversations")
search_query = st.sidebar.text_input("🔍 Search", placeholder="Type to filter...")
if st.sidebar.button('➕ Start New Chat'):
    # Create the new chat in the database
    run_async(create_new_chat_in_db(st.session_state['username']))
    # Immediately re-fetch all threads to update the sidebar
    threads, names = run_async(retrieve_all_threads_db(st.session_state['username']))
    st.session_state['chat_threads'] = threads
    st.session_state['thread_names'] = names
    st.rerun()

# ---------------- Sidebar RAG Upload ----------------
st.sidebar.markdown("---")
st.sidebar.markdown("### 📄 Document RAG")

current_doc_info = st.session_state.get('current_doc_info')
if current_doc_info:
    doc_meta = current_doc_info.get('doc_info', {})
    st.sidebar.success(
        f"Using `{current_doc_info.get('filename')}` "
        f"({doc_meta.get('chunks')} chunks from {doc_meta.get('documents')} pages)"
    )
else:
    st.sidebar.info("No PDF indexed for this chat.")

uploaded_pdf = st.sidebar.file_uploader("Upload a PDF for this chat", type=["pdf"], key="pdf_uploader")
if uploaded_pdf:
    if current_doc_info and current_doc_info.get('filename') == uploaded_pdf.name:
        st.sidebar.info(f"`{uploaded_pdf.name}` already processed for this chat.")
    else:
        with st.sidebar.status("Indexing PDF…", expanded=True) as status_box:
            try:
                summary = run_async(ingest_pdf(
                    file_bytes=uploaded_pdf.getvalue(),
                    thread_id=st.session_state['thread_id'],
                    filename=uploaded_pdf.name
                ))
                st.session_state['current_doc_info'] = {"filename": uploaded_pdf.name, "doc_info": summary}
                status_box.update(label="✅ PDF indexed", state="complete", expanded=False)
                st.rerun()
            except Exception as e:
                status_box.update(label=f"❌ Error indexing PDF: {e}", state="error", expanded=True)


# ---------------- Sidebar Threads ----------------
filtered_threads = [
    tid for tid in st.session_state.get('chat_threads', [])
    if search_query.lower() in st.session_state.get('thread_names', {}).get(str(tid), "").lower()
]

for thread_id in filtered_threads[::-1]:
    container = st.sidebar.container()
    current_name = st.session_state.get('thread_names', {}).get(str(thread_id), f"Conversation {thread_id}")

    col1, col2 = container.columns([0.85, 0.15])
    with col1:
        if st.button(current_name, key=f"name_{thread_id}", use_container_width=True):
            st.session_state['thread_id'] = thread_id
            messages = run_async(load_conversation_from_checkpointer(str(thread_id)))
            st.session_state['message_history'] = format_messages(messages)
            st.session_state['current_doc_info'] = run_async(get_document_for_thread(str(thread_id)))
            st.rerun()
            
    with col2:
        if st.button("⋮", key=f"slider_btn_{thread_id}", use_container_width=True):
            st.session_state[f"slider_{thread_id}"] = not st.session_state.get(f"slider_{thread_id}", False)
            st.rerun()

    if st.session_state.get(f"slider_{thread_id}", False):
        is_editing = st.session_state.get(f"editing_{thread_id}", False)
        is_confirming_delete = st.session_state.get(f"confirm_delete_{thread_id}", False)

        if is_editing:
            c1, c2 = container.columns([0.7, 0.3])
            new_name = c1.text_input("New name", value=current_name, key=f"rename_value_{thread_id}", label_visibility="collapsed")
            if c2.button("💾", key=f"save_{thread_id}"):
                if new_name.strip() and new_name.strip() != current_name:
                    st.session_state['thread_names'][str(thread_id)] = new_name
                    run_async(store_conversation_name(thread_id, st.session_state['username'], new_name))
                st.session_state[f"editing_{thread_id}"] = False
                st.session_state[f"slider_{thread_id}"] = False
                st.rerun()

        elif is_confirming_delete:
            container.warning("Delete this chat?")
            c1, c2 = container.columns(2)
            if c1.button("Yes, Delete", key=f"confirm_btn_{thread_id}", use_container_width=True):
                active_thread_was_deleted = st.session_state.get('thread_id') == thread_id
                
                # Update UI state first
                st.session_state['chat_threads'].remove(thread_id)
                st.session_state['thread_names'].pop(str(thread_id), None)
                
                # Delete from DB
                run_async(delete_conversation(str(thread_id), st.session_state['username']))
                
                if active_thread_was_deleted:
                    # If there are other chats, switch to the latest one. Otherwise, create a new one.
                    if st.session_state['chat_threads']:
                        st.session_state['thread_id'] = st.session_state['chat_threads'][-1]
                        st.session_state['current_doc_info'] = run_async(get_document_for_thread(str(st.session_state['thread_id'])))
                    else:
                        run_async(create_new_chat_in_db(st.session_state['username']))
                        # Re-fetch to get the new chat's ID and name
                        threads, names = run_async(retrieve_all_threads_db(st.session_state['username']))
                        st.session_state['chat_threads'] = threads
                        st.session_state['thread_names'] = names

                st.rerun()
            
            if c2.button("Cancel", key=f"cancel_delete_{thread_id}", use_container_width=True):
                st.session_state[f"confirm_delete_{thread_id}"] = False
                st.session_state[f"slider_{thread_id}"] = False
                st.rerun()

        else:
            c1, c2 = container.columns(2)
            if c1.button("✏️ Edit", key=f"edit_{thread_id}", use_container_width=True):
                st.session_state[f"editing_{thread_id}"] = True
                st.rerun()
            
            if c2.button("🗑️ Delete", key=f"delete_{thread_id}", use_container_width=True):
                st.session_state[f"confirm_delete_{thread_id}"] = True
                st.rerun()

# ---------------- Main Chat ----------------
st.title("💬 LangGraph Chat")
# Add a guard in case message_history is None
for message in st.session_state.get('message_history', []):
    with st.chat_message(message['role']):
        st.markdown(message['content'], unsafe_allow_html=True)

user_input = st.chat_input("Type your message...")
if user_input:
    current_username = st.session_state.get("username")
    if not current_username:
        st.error("User not logged in. Please refresh and log in again.")
        st.stop()

    # Check limit before incrementing
    if st.session_state.get('ai_counter', 0) >= MAX_AI_SEARCHES:
        st.warning(f"You have reached the daily limit.")
    else:
        new_count = run_async(increment_ai_count(current_username))
        st.session_state['ai_counter'] = new_count
        cookies["ai_counter"] = str(new_count)
        cookies.save()

        st.session_state['message_history'].append({'role':'user','content':user_input})
        with st.chat_message('user'):
            st.markdown(user_input, unsafe_allow_html=True)

        CONFIG = {"configurable":{"thread_id": str(st.session_state["thread_id"])}}
        
        with st.chat_message('assistant'):
            status_holder = {"box": None}
            
            def ai_only_stream():
                event_queue = queue.Queue()
                async def run_stream():
                    try:
                        async for event in chatbot.astream_events(
                            {'messages':[HumanMessage(content=user_input)]},
                            config=CONFIG,
                            version="v1"
                        ):
                            event_queue.put(event)
                    except Exception as e:
                        event_queue.put({"event": "error", "data": e})
                    finally:
                        event_queue.put(None)
                
                submit_async_task(run_stream())

                while True:
                    event = event_queue.get()
                    if event is None: break
                    if event['event'] == 'on_chat_model_stream':
                        chunk = event['data']['chunk']
                        if isinstance(chunk, AIMessageChunk) and chunk.content:
                            yield chunk.content
                    if event['event'] == 'on_tool_start':
                        tool_name = event['name']
                        if status_holder["box"] is None:
                            status_holder["box"] = st.status(f"🔧 Using `{tool_name}` …")
                        else:
                            status_holder["box"].update(label=f"🔧 Using `{tool_name}` …")

            ai_message = st.write_stream(ai_only_stream())
            
            if status_holder["box"] is not None:
                status_holder["box"].update(label="✅ Tool finished", state="complete")

        st.session_state['message_history'].append({'role':'assistant','content':ai_message})
        
        run_async(store_conversation(
            str(st.session_state['thread_id']),
            current_username,
            st.session_state['message_history'],
            st.session_state['thread_names'][str(st.session_state['thread_id'])]
        ))
        
        st.rerun()
