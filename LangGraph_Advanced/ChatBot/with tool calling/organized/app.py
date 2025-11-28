import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager


from langgraph_tool_backend import (
    chatbot, load_conversation, store_conversation,
    retrieve_all_threads, store_conversation_name,
    register_user, login_user, increment_ai_count, delete_conversation
)
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


import uuid
import json


MAX_AI_SEARCHES = 50

# ---------------- Cookie Setup ----------------
cookies = EncryptedCookieManager(
    prefix="langgraph_", password="7b9561efc4a6acf95c78285418225434533f70dd609026c8ff9ba1c50a5be6c6"
)
if not cookies.ready():
    st.stop()  # wait for cookie initialization

# ---------------- Thread & Session Functions ----------------
def generate_thread_id():
    return uuid.uuid4()

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    st.session_state['message_history'] = []
    conversation_count = len(st.session_state.get('chat_threads', [])) + 1
    default_name = f"Conversation {conversation_count}"
    st.session_state.setdefault('thread_names', {})[str(thread_id)] = default_name

    store_conversation(str(thread_id), st.session_state['username'], [], default_name)
    st.session_state.setdefault('chat_threads', []).append(thread_id)
    st.session_state[f"slider_{thread_id}"] = False
    st.session_state[f"editing_{thread_id}"] = False
    st.session_state[f"confirm_delete_{thread_id}"] = False

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

# ---------------- Restore from Cookie ----------------
if cookies.get("username") and cookies.get("logged_in") == "True":
    st.session_state['logged_in'] = True
    st.session_state['username'] = cookies.get("username")
    st.session_state['ai_counter'] = int(cookies.get("ai_counter", 0))
    st.session_state['chat_threads'], st.session_state['thread_names'] = retrieve_all_threads(st.session_state['username'])
    if st.session_state['chat_threads']:
        st.session_state['thread_id'] = st.session_state['chat_threads'][-1]
        st.session_state['message_history'] = load_conversation(str(st.session_state['thread_id']), st.session_state['username'])
    else:
        reset_chat()

# ---------------- Logout ----------------
def logout():
    st.session_state.clear()
    
    cookies["username"] = ""
    cookies["logged_in"] = "False"
    cookies["ai_counter"] = "0"
    cookies.save()
    
    # Show login page again
    st.session_state['logged_in'] = False
   


# ---------------- Login/Register ----------------
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'> Welcome to <span style='color:#2563eb;'>LangGraph </span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Your personal AI-powered chat assistant 🚀</p>", unsafe_allow_html=True)

    
   
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("🌟 Login to continue")
       
        username_login = st.text_input("Username", key="login_user")
        password_login = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            res = login_user(username_login, password_login)
            if res["success"]:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username_login
                st.session_state['ai_counter'] = res.get("ai_count", 0)
                st.session_state['chat_threads'], st.session_state['thread_names'] = retrieve_all_threads(username_login)
                if st.session_state['chat_threads']:
                    st.session_state['thread_id'] = st.session_state['chat_threads'][-1]
                    st.session_state['message_history'] = load_conversation(str(st.session_state['thread_id']), username_login)
                else:
                    reset_chat()
                
                # Save session to cookies
                cookies["username"] = username_login
                cookies["logged_in"] = "True"
                cookies["ai_counter"] = str(st.session_state['ai_counter'])
                cookies.save()
                st.success(f"Welcome, {username_login}!")
                
            else:
                st.error(res["error"])

    with tab2:
        st.subheader("🆕 Create a new account")
        username_reg = st.text_input("Choose username", key="reg_user")
        password_reg = st.text_input("Choose password", type="password", key="reg_pass")
        if st.button("Register"):
            res = register_user(username_reg.strip(), password_reg.strip())
            if res["success"]:
                st.success(f"User {username_reg} registered successfully!")
            else:
                st.error(res["error"])

    st.stop()

# ---------------- Sidebar ----------------
def render_sidebar():
    st.sidebar.title('🤖 LangGraph Chatbot')
    st.sidebar.button("🔒 Logout", on_click=logout)
    st.sidebar.markdown("# 💬 My Conversations")
    search_query = st.sidebar.text_input("🔍 Search", placeholder="Type to filter...")
    if st.sidebar.button('➕ Start New Chat'):
        reset_chat()

    
    return search_query

search_query = render_sidebar()

# ---------------- Sidebar Threads ----------------
filtered_threads = [
    tid for tid in st.session_state['chat_threads']
    if search_query.lower() in st.session_state['thread_names'].get(str(tid), "").lower()
]

for thread_id in filtered_threads[::-1]:
    container = st.sidebar.container()
    cols = container.columns([4, 1])
    current_name = st.session_state['thread_names'].get(str(thread_id), f"Conversation {thread_id}")

    # Switch thread
    if cols[0].button(current_name, key=f"name_{thread_id}"):
        st.session_state['thread_id'] = thread_id
        st.session_state['message_history'] = load_conversation(str(thread_id), st.session_state['username'])

    # Toggle slider
    if cols[1].button("⋮", key=f"slider_btn_{thread_id}"):
        st.session_state[f"slider_{thread_id}"] = not st.session_state.get(f"slider_{thread_id}", False)
        st.session_state[f"editing_{thread_id}"] = False
        st.session_state[f"confirm_delete_{thread_id}"] = False

    if st.session_state.get(f"slider_{thread_id}", False):
        with container:
            confirm_open = st.session_state.get(f"confirm_delete_{thread_id}", False)

            # Rename
            if st.session_state.get(f"editing_{thread_id}", False) and not confirm_open:
                def save_rename(thread_id=thread_id):
                    new_name = st.session_state[f"rename_value_{thread_id}"].strip()
                    old_name = st.session_state['thread_names'].get(str(thread_id), "")
                    if new_name and new_name != old_name:
                        st.session_state['thread_names'][str(thread_id)] = new_name
                        store_conversation_name(thread_id, st.session_state['username'], new_name)
                        st.toast("✅ Renamed successfully", icon="✅")
                    st.session_state[f"editing_{thread_id}"] = False
                    st.session_state[f"slider_{thread_id}"] = False

                st.text_input(
                    "✏️ Rename",
                    value=current_name,
                    key=f"rename_value_{thread_id}",
                    label_visibility="collapsed",
                    on_change=save_rename
                )

            # Edit/Delete buttons
            if not confirm_open:
                col1, col2 = st.columns([1, 1])
                if not st.session_state.get(f"editing_{thread_id}", False):
                    if col1.button("🖉 Edit", key=f"edit_{thread_id}"):
                        st.session_state[f"editing_{thread_id}"] = True
                else:
                    if col1.button("💾 Save", key=f"save_{thread_id}"):
                        save_rename()

                if col2.button("🗑 Delete", key=f"delete_{thread_id}"):
                    st.session_state[f"confirm_delete_{thread_id}"] = True

           # Confirm Delete
            if confirm_open:
                st.warning("Are you sure you want to delete?")
                c1, c2 = st.columns([1, 1])
                if c1.button("Cancel", key=f"cancel_delete_{thread_id}"):
                    st.session_state[f"confirm_delete_{thread_id}"] = False
                    st.session_state[f"slider_{thread_id}"] = False
                    st.session_state[f"editing_{thread_id}"] = False
                    st.toast("❎ Delete cancelled", icon="❎")
                if c2.button("Confirm", key=f"confirm_btn_{thread_id}"):
                    # Remove from frontend
                    st.session_state['chat_threads'].remove(thread_id)
                    st.session_state['thread_names'].pop(str(thread_id), None)
                    st.session_state['message_history'] = []

                    # Fully delete from backend
                    delete_conversation(str(thread_id), st.session_state['username'])

                    st.toast("❌ Thread deleted", icon="❌")

# ---------------- Main Chat ----------------
st.title("💬 LangGraph Chat")
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'], unsafe_allow_html=True)

user_input = st.chat_input("Type your message...")
if user_input:
    # --- Check AI usage limit ---
    if st.session_state['ai_counter'] >= MAX_AI_SEARCHES:
        st.warning(f"You have reached the daily limit .")
    else:
        st.session_state['message_history'].append({'role':'user','content':user_input})
        with st.chat_message('user'):
            st.markdown(user_input, unsafe_allow_html=True)

        CONFIG = {"configurable":{"thread_id": str(st.session_state["thread_id"])}}
        with st.chat_message('assistant'):
            status_holder = {"box": None}
            def ai_only_stream():
                
                    for message_chunk, metadata in chatbot.stream(
                        {'messages':[HumanMessage(content=user_input)]},
                        config=CONFIG,
                        stream_mode='messages'
                    ):
                        if isinstance(message_chunk, ToolMessage):
                            tool_name = getattr(message_chunk, "name", "tool")
                            if status_holder["box"] is None:
                                status_holder["box"] = st.status(f"🔧 Using `{tool_name}` …", expanded=True)
                            else:
                                status_holder["box"].update(label=f"🔧 Using `{tool_name}` …", state="running", expanded=True)
                        elif isinstance(message_chunk, AIMessage):
                            #print(f"Message Type: {type(message_chunk)}, Content: {message_chunk.content}") # Debug print
                            yield message_chunk.content
                
                
                    # Finalize the status box
                    if status_holder["box"] is not None:
                        status_holder["box"].update(label="✅ Tool finished", state="complete", expanded=False)
            
            ai_message = st.write_stream(ai_only_stream())


        st.session_state['message_history'].append({'role':'assistant','content':ai_message})
        store_conversation(
            str(st.session_state['thread_id']),
            st.session_state['username'],
            st.session_state['message_history'],
            st.session_state['thread_names'][str(st.session_state['thread_id'])]
        )

        # Increment AI usage
        st.session_state['ai_counter'] = increment_ai_count(st.session_state['username'])
        # Persist AI counter in cookie
        cookies["ai_counter"] = str(st.session_state['ai_counter'])
        cookies.save()
