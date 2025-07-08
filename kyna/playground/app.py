import streamlit as st
import requests
import json
import uuid
import os
from typing import Dict, Any, Optional

# Configure Streamlit page
st.set_page_config(
    page_title="Kyna FAQ Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "use_session" not in st.session_state:
        st.session_state.use_session = True

def ask_question(question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Send question to the API."""
    payload = {"question": question}
    if session_id:
        payload["session_id"] = session_id
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/ask",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with API: {str(e)}")
        return None

def get_documents() -> Dict[str, Any]:
    """Get list of documents from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/documents")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching documents: {str(e)}")
        return None

def upload_document(file) -> bool:
    """Upload a document to the API."""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        response = requests.post(
            f"{API_BASE_URL}/documents/upload",
            files=files
        )
        response.raise_for_status()
        result = response.json()
        st.success(f"Document uploaded successfully! ID: {result['doc_id']}")
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Error uploading document: {str(e)}")
        return False

def delete_document(doc_id: int) -> bool:
    """Delete a document via API."""
    try:
        response = requests.delete(f"{API_BASE_URL}/documents/{doc_id}")
        response.raise_for_status()
        st.success("Document deleted successfully!")
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Error deleting document: {str(e)}")
        return False

def display_chat_message(role: str, content: str, sources: Optional[list] = None):
    """Display a chat message with optional sources."""
    with st.chat_message(role):
        st.write(content)
        if sources and role == "assistant":
            with st.expander("📚 Sources"):
                for i, source in enumerate(sources, 1):
                    st.write(f"**Source {i}:**")
                    st.write(source["page_content"][:500] + "..." if len(source["page_content"]) > 500 else source["page_content"])
                    if source["metadata"]:
                        st.json(source["metadata"])

def main():
    """Main application function."""
    init_session_state()
    
    st.title("🤖 Kyna FAQ Assistant")
    st.markdown("*AI-powered FAQ assistant using RAG with LangChain*")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Session settings
        st.subheader("Conversation Settings")
        st.session_state.use_session = st.checkbox(
            "Use conversational memory",
            value=st.session_state.use_session,
            help="Enable to maintain context across questions"
        )
        
        if st.session_state.use_session:
            st.info(f"Session ID: {st.session_state.session_id[:8]}...")
            if st.button("🔄 New Session"):
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.messages = []
                st.rerun()
        
        # Clear chat
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        # Document management
        st.subheader("📄 Document Management")
        
        # Upload document
        uploaded_file = st.file_uploader(
            "Upload Document",
            type=['pdf', 'txt', 'md', 'docx'],
            help="Upload a document to add to the knowledge base"
        )
        
        if uploaded_file is not None:
            if st.button("📤 Upload"):
                if upload_document(uploaded_file):
                    st.rerun()
        
        # List documents
        if st.button("📋 Refresh Documents"):
            st.rerun()
        
        # Get and display documents
        docs_data = get_documents()
        if docs_data:
            st.write(f"**Total Documents:** {docs_data['total']}")
            
            if docs_data['documents']:
                st.subheader("Existing Documents")
                for doc in docs_data['documents']:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"📄 {doc['filename']}")
                        st.caption(f"Type: {doc['document_type']} | ID: {doc['doc_id']}")
                    with col2:
                        if st.button("🗑️", key=f"delete_{doc['doc_id']}", help="Delete document"):
                            if delete_document(doc['doc_id']):
                                st.rerun()
    
    # Main chat interface
    st.header("💬 Chat")
    
    # Display chat history
    for message in st.session_state.messages:
        display_chat_message(
            message["role"],
            message["content"],
            message.get("sources")
        )
    
    # Chat input
    if prompt := st.chat_input("Ask a question..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        display_chat_message("user", prompt)
        
        # Get response from API
        session_id = st.session_state.session_id if st.session_state.use_session else None
        
        with st.spinner("Thinking..."):
            response = ask_question(prompt, session_id)
        
        if response:
            # Add assistant response to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response["answer"],
                "sources": response["source_documents"]
            })
            display_chat_message("assistant", response["answer"], response["source_documents"])
        else:
            st.error("Failed to get response from the assistant.")

if __name__ == "__main__":
    main()