import time
from typing import Dict, Any, Optional, List
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from .config import get_config
from .llm import get_llm, get_condensing_llm
from .retriever import get_retriever

class SessionMemoryManager:
    """Manages conversational memory sessions with TTL."""
    
    def __init__(self):
        self.config = get_config()
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """Get or create memory for a session."""
        current_time = time.time()
        
        # Clean expired sessions
        self._cleanup_expired_sessions(current_time)
        
        # Get or create session
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "memory": ConversationBufferWindowMemory(
                    k=self.config.memory.max_history_length,
                    memory_key="chat_history",
                    return_messages=True
                ),
                "last_access": current_time
            }
        else:
            self.sessions[session_id]["last_access"] = current_time
        
        return self.sessions[session_id]["memory"]
    
    def _cleanup_expired_sessions(self, current_time: float):
        """Remove expired sessions."""
        expired_sessions = []
        for session_id, session_data in self.sessions.items():
            if current_time - session_data["last_access"] > self.config.memory.ttl_seconds:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]

class RAGChain:
    """Main RAG chain handler supporting both stateful and stateless modes."""
    
    def __init__(self):
        self.config = get_config()
        self.llm = get_llm()
        self.condensing_llm = get_condensing_llm()
        self.retriever = get_retriever()
        self.session_manager = SessionMemoryManager()
        
        # Create prompt template
        self.prompt_template = PromptTemplate(
            template=self.config.rag.prompt_template,
            input_variables=["context", "question"]
        )
    
    def ask_stateless(self, question: str) -> Dict[str, Any]:
        """Handle stateless question (no session memory)."""
        # Create RetrievalQA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.prompt_template}
        )
        
        # Get response
        response = qa_chain.invoke({"query": question})
        
        return {
            "question": question,
            "answer": response["result"],
            "source_documents": [
                {
                    "page_content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in response["source_documents"]
            ]
        }
    
    def ask_stateful(self, question: str, session_id: str) -> Dict[str, Any]:
        """Handle stateful question (with session memory)."""
        # Get session memory
        memory = self.session_manager.get_memory(session_id)
        
        # Create ConversationalRetrievalChain
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            condense_question_llm=self.condensing_llm,
            retriever=self.retriever,
            memory=memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": self.prompt_template}
        )
        
        # Get response
        response = qa_chain.invoke({"question": question})
        
        return {
            "question": question,
            "answer": response["answer"],
            "source_documents": [
                {
                    "page_content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in response["source_documents"]
            ]
        }
    
    def ask(self, question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Main ask method that routes to stateful or stateless processing."""
        if session_id:
            return self.ask_stateful(question, session_id)
        else:
            return self.ask_stateless(question)
    
    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session."""
        if session_id not in self.session_manager.sessions:
            return []
        
        memory = self.session_manager.sessions[session_id]["memory"]
        messages = memory.chat_memory.messages
        
        history = []
        for message in messages:
            if isinstance(message, HumanMessage):
                history.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                history.append({"role": "assistant", "content": message.content})
        
        return history
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a specific session."""
        if session_id in self.session_manager.sessions:
            del self.session_manager.sessions[session_id]
            return True
        return False

# Global RAG chain instance
_rag_chain: Optional[RAGChain] = None

def get_rag_chain() -> RAGChain:
    """Get singleton RAG chain instance."""
    global _rag_chain
    if _rag_chain is None:
        _rag_chain = RAGChain()
    return _rag_chain