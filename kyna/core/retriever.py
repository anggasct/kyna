"""
Retriever Module - Manages document retrieval from the vector store.

This module is responsible for connecting to the Qdrant vector database
and configuring the retriever component of the RAG pipeline. It ensures
that relevant document chunks can be efficiently fetched based on user queries.

Key components:
- `_ensure_collection_exists`: Helper to ensure the Qdrant collection is ready.
- `get_retriever`: Provides a configured LangChain retriever instance.
- `get_vector_store`: Provides the raw Qdrant vector store instance.

Integration:
- Uses `config` for Qdrant connection details and retriever settings.
- Interacts with `embedder` to get embedding models for the vector store.
- Used by `rag_chain` to retrieve documents.
"""
import logging
from langchain_community.vectorstores import Qdrant
from langchain_core.vectorstores import VectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from .config import get_config
from .embedder import get_langchain_embeddings

logger = logging.getLogger(__name__)

def _ensure_collection_exists(client: QdrantClient, collection_name: str):
    try:
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if collection_name not in collection_names:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
    except Exception as e:
        logger.error(f"Error ensuring collection exists: {str(e)}", exc_info=True)
        raise

def get_retriever():
    config = get_config()
    
    client = QdrantClient(
        host=config.qdrant.host,
        port=config.qdrant.port
    )
    
    _ensure_collection_exists(client, config.qdrant.collection_name)
    
    embeddings = get_langchain_embeddings()
    
    vector_store = Qdrant(
        client=client,
        collection_name=config.qdrant.collection_name,
        embeddings=embeddings
    )
    
    if config.rag.retriever.search_type == "similarity":
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": config.rag.retriever.search_k}
        )
    elif config.rag.retriever.search_type == "similarity_score_threshold":
        retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": config.rag.retriever.search_k,
                "score_threshold": config.rag.retriever.score_threshold
            }
        )
    else:
        raise ValueError(f"Unsupported search type: {config.rag.retriever.search_type}")
    
    return retriever

def get_vector_store() -> VectorStore:
    config = get_config()
    
    client = QdrantClient(
        host=config.qdrant.host,
        port=config.qdrant.port
    )
    
    _ensure_collection_exists(client, config.qdrant.collection_name)
    
    embeddings = get_langchain_embeddings()
    
    vector_store = Qdrant(
        client=client,
        collection_name=config.qdrant.collection_name,
        embeddings=embeddings
    )
    
    return vector_store