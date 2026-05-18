import streamlit as st
import requests
import pandas as pd
import os

# The URL where the FastAPI server is running.
# Local development defaults to localhost; Docker Compose overrides this to http://backend:8000.
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# --- Page Configuration ---
st.set_page_config(
    page_title="RAG Document Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for minor tweaks
st.markdown("""
    <style>
        .stChatInputContainer { padding-bottom: 20px; }
        .st-emotion-cache-1c7y2kd { flex-direction: row-reverse; }
    </style>
""", unsafe_allow_html=True)

st.title("📚 RAG Document Assistant")
st.caption("Upload PDFs, track their processing status, and query the embedded knowledge base.")

# --- Session State Management ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# Create clean tabs for the UI
tab_upload, tab_status, tab_chat = st.tabs(["📤 Upload Documents", "📊 Processing Status", "💬 Chat with Documents"])

# ==========================================
# TAB 1: UPLOAD DOCUMENTS
# ==========================================
with tab_upload:
    st.header("Upload PDFs for Processing")

    with st.container(border=True):
        uploaded_files = st.file_uploader("Select multiple PDFs to ingest into the vector database.", type="pdf",
                                          accept_multiple_files=True)

        if st.button("Upload to Backend", type="primary", use_container_width=True):
            if not uploaded_files:
                st.warning("⚠️ Please select at least one file first.")
            else:
                with st.spinner(f"Uploading {len(uploaded_files)} file(s)..."):
                    files_payload = [
                        ("files", (file.name, file.getvalue(), "application/pdf"))
                        for file in uploaded_files
                    ]

                    try:
                        response = requests.post(f"{API_BASE_URL}/upload", files=files_payload)
                        if response.status_code == 200:
                            st.success(f"✅ {response.json()['message']}")
                        else:
                            st.error(f"❌ Upload failed: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("🔌 Failed to connect to the backend. Is your FastAPI server running?")

# ==========================================
# TAB 2: PROCESSING STATUS
# ==========================================
with tab_status:
    col1, col2 = st.columns([8, 2])
    with col1:
        st.header("Database Metadata")
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            pass

    try:
        response = requests.get(f"{API_BASE_URL}/metadata")
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                df = df[['id', 'filename', 'status', 'chunk_count', 'upload_date', 'error_message']]


                def highlight_status(val):
                    color = '#10B981' if val == 'completed' else '#F59E0B' if val == 'processing' else '#EF4444' if val == 'failed' else '#6B7280'
                    return f'color: {color}; font-weight: 600'


                st.dataframe(df.style.map(highlight_status, subset=['status']), use_container_width=True,
                             hide_index=True)
            else:
                st.info("No documents have been uploaded yet.")
        else:
            st.error("Failed to fetch metadata from the server.")
    except Exception:
        st.error("🔌 Backend is currently offline.")

# ==========================================
# TAB 3: CHAT INTERFACE
# ==========================================
with tab_chat:
    # Header controls with cleaner layout
    col_info, col_clear = st.columns([4, 1], vertical_alignment="center")
    with col_info:
        if st.session_state.thread_id:
            st.caption(f"🧠 **Active Memory Thread:** `{st.session_state.thread_id}`")
        else:
            st.caption("✨ **New Session:** Ask a question to start a new memory thread.")

    with col_clear:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.thread_id = None
            st.rerun()

    st.divider()

    # Empty State Welcome Message
    if not st.session_state.messages:
        st.info(
            "👋 **Welcome!** Once you've uploaded your documents in the first tab, you can ask me questions about them right here. I'll remember the context of our conversation.")

    # Avatar mapping for a better visual experience
    avatar_map = {"user": "👤", "assistant": "🤖"}

    # 1. Display existing chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=avatar_map.get(message["role"])):
            st.markdown(message["content"])

    # 2. Accept new user input
    if prompt := st.chat_input("Ask a question about your uploaded documents..."):

        # Add user message to UI and state
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # 3. Call the API
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()

            with st.spinner("Searching documents & generating response..."):
                payload = {"question": prompt}
                if st.session_state.thread_id:
                    payload["thread_id"] = st.session_state.thread_id

                try:
                    response = requests.post(f"{API_BASE_URL}/query", json=payload)

                    if response.status_code == 200:
                        data = response.json()
                        answer = data["answer"]

                        # Typewriter effect for standard markdown output
                        message_placeholder.markdown(answer)

                        st.session_state.thread_id = data["thread_id"]
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        st.error(f"API Error: {response.text}")
                except Exception:
                    st.error("🔌 Failed to connect to the backend API.")
