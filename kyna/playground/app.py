import streamlit as st
import requests
import json
import uuid
import os
from typing import Dict, Any, Optional

st.set_page_config(
    page_title="Kyna - AI Knowledge Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "use_session" not in st.session_state:
        st.session_state.use_session = True

def ask_question(question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
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
    try:
        response = requests.get(f"{API_BASE_URL}/documents")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching documents: {str(e)}")
        return None

def upload_document(file) -> bool:
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

def add_url_document(url: str, filename: str = None) -> bool:
    try:
        payload = {"url": url}
        if filename:
            payload["filename"] = filename
        
        response = requests.post(
            f"{API_BASE_URL}/documents/add-url",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        result = response.json()
        st.success(f"URL document processed successfully! ID: {result['doc_id']}")
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Error processing URL document: {str(e)}")
        return False

def delete_document(doc_id: int) -> bool:
    try:
        response = requests.delete(f"{API_BASE_URL}/documents/{doc_id}")
        response.raise_for_status()
        st.success("Document deleted successfully!")
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Error deleting document: {str(e)}")
        return False

def display_chat_message(role: str, content: str, sources: Optional[list] = None):
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
    init_session_state()
    
    st.title("🤖 Kyna - AI Knowledge Assistant")
    st.markdown("***K**now **Y**our **N**ext **A**nswer - AI-powered knowledge assistant using RAG with LangChain*")
    
    with st.sidebar:
        st.header("⚙️ Settings")
        
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
        
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        st.subheader("📄 Document Management")
        
        # Document source tabs
        doc_tab1, doc_tab2 = st.tabs(["📁 File Upload", "🌐 URL"])
        
        with doc_tab1:
            uploaded_file = st.file_uploader(
                "Upload Document",
                type=['pdf', 'txt', 'md', 'docx'],
                help="Upload a document to add to the knowledge base",
                key="document_uploader"
            )
            
            if uploaded_file is not None:
                if st.button("📤 Upload", key="upload_file"):
                    if upload_document(uploaded_file):
                        # Clear the file uploader by removing it from session state
                        if "document_uploader" in st.session_state:
                            del st.session_state["document_uploader"]
                        st.rerun()
        
        with doc_tab2:
            url_input = st.text_input(
                "Document URL",
                placeholder="https://example.com/document.html",
                help="Enter a URL to extract content from web pages"
            )
            
            filename_input = st.text_input(
                "Custom Filename (optional)",
                placeholder="my-document.html",
                help="Optional: Provide a custom filename for the URL document"
            )
            
            if st.button("🌐 Add URL", key="add_url"):
                if url_input.strip():
                    filename = filename_input.strip() if filename_input.strip() else None
                    if add_url_document(url_input.strip(), filename):
                        st.rerun()
                else:
                    st.error("Please enter a valid URL")
        
        if st.button("📋 Refresh Documents"):
            st.rerun()
        
        docs_data = get_documents()
        if docs_data:
            st.write(f"**Total Documents:** {docs_data['total']}")
            
            if docs_data['documents']:
                st.subheader("Existing Documents")
                for doc in docs_data['documents']:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        # Display different icons based on source type
                        icon = "📁" if doc.get('source_type') == 'file' else "🌐"
                        st.write(f"{icon} {doc['filename']}")
                        
                        # Show source type and URL
                        source_info = f"Type: {doc['document_type']} | Source: {doc.get('source_type', 'file')} | ID: {doc['doc_id']}"
                        st.caption(source_info)
                        
                        # Show clickable URL for files or actual URL for web documents
                        if doc.get('source_url'):
                            if doc.get('source_type') == 'file':
                                st.caption(f"📎 [Download file]({doc['source_url']})")
                            else:
                                st.caption(f"🔗 [Original URL]({doc['source_url']})")
                    
                    with col2:
                        if st.button("🗑️", key=f"delete_{doc['doc_id']}", help="Delete document"):
                            if delete_document(doc['doc_id']):
                                st.rerun()
    
    st.header("💬 Chat")
    
    for message in st.session_state.messages:
        display_chat_message(
            message["role"],
            message["content"],
            message.get("sources")
        )
    
    if prompt := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        display_chat_message("user", prompt)
        
        session_id = st.session_state.session_id if st.session_state.use_session else None
        
        with st.spinner("Thinking..."):
            response = ask_question(prompt, session_id)
        
        if response:
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