"""
RAG Chain Module - Orchestrates the Retrieval-Augmented Generation process.

This module provides the core logic for processing user questions, retrieving relevant
documents, and generating answers using Large Language Models (LLMs). It supports
both stateless and stateful (conversational memory) interactions.

Key components:
- `SessionMemoryManager`: Manages conversational history for sessions.
- `RAGChain`: Main class orchestrating the RAG pipeline.

Integration:
- Uses `config` for configuration settings.
- Interacts with `llm` for language model operations.
- Utilizes `retriever` for document retrieval from the vector store.
"""
import time
import logging
import os
from typing import Dict, Any, Optional, List
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from .config import get_config
from .llm import get_llm, get_condensing_llm
from .retriever import get_retriever

logger = logging.getLogger(__name__)

class SessionMemoryManager:
    """Manages conversational memory sessions."""
    
    def __init__(self):
        self.config = get_config()
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        current_time = time.time()
        self._cleanup_expired_sessions(current_time)
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "memory": ConversationBufferWindowMemory(
                    k=self.config.memory.max_history_length,
                    memory_key="chat_history",
                    return_messages=True,
                    output_key="answer"
                ),
                "last_access": current_time
            }
        else:
            self.sessions[session_id]["last_access"] = current_time
        
        return self.sessions[session_id]["memory"]
    
    def _cleanup_expired_sessions(self, current_time: float):
        expired_sessions = []
        for session_id, session_data in self.sessions.items():
            if current_time - session_data["last_access"] > self.config.memory.ttl_seconds:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]

class RAGChain:
    """Main RAG chain handler."""
    
    def __init__(self):
        self.config = get_config()
        self.llm = get_llm()
        self.condensing_llm = get_condensing_llm()
        self.retriever = get_retriever()
        self.session_manager = SessionMemoryManager()
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> PromptTemplate:
        prompt_path = self.config.rag.prompt_template
        
        if os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as f:
                template = f.read().strip()
            return PromptTemplate(
                template=template,
                input_variables=["context", "question"]
            )
        else:
            logger.warning(f"Prompt file not found: {prompt_path}")
            return PromptTemplate(
                template="Use the following context to answer the question:\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:",
                input_variables=["context", "question"]
            )
    
    
    def ask_stateless(self, question: str) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"Processing stateless question: {question}")
        
        prompt_template = self.prompt_template
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt_template}
        )
        
        response = qa_chain.invoke({"query": question})
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Request completed in {duration:.2f}s")
        
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
        start_time = time.time()
        logger.info(f"Processing stateful question: {question} (session: {session_id})")
        
        try:
            prompt_template = self.prompt_template
            
            memory = self.session_manager.get_memory(session_id)
            
            qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                condense_question_llm=self.condensing_llm,
                retriever=self.retriever,
                memory=memory,
                return_source_documents=True,
                combine_docs_chain_kwargs={"prompt": prompt_template},
                output_key="answer"
            )
            
            response = qa_chain.invoke({"question": question})
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"Conversational request completed in {duration:.2f}s")
            
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
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"Error in ask_stateful after {duration:.2f}s: {e}")
            
            return {
                "question": question,
                "answer": f"Error processing question: {str(e)}",
                "source_documents": [],
                "error": True
            }
    
    def ask(self, question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        return self.ask_stateful(question, session_id) if session_id else self.ask_stateless(question)
    
    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
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
        if session_id in self.session_manager.sessions:
            del self.session_manager.sessions[session_id]
            return True
        return False

_rag_chain: Optional[RAGChain] = None

def get_rag_chain() -> RAGChain:
    global _rag_chain
    if _rag_chain is None:
        _rag_chain = RAGChain()
    return _rag_chain