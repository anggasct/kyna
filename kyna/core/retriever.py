from langchain_community.vectorstores import Qdrant
from langchain_core.vectorstores import VectorStore
from qdrant_client import QdrantClient
from .config import get_config
from .embedder import get_langchain_embeddings

def get_retriever():
    """Get the configured Qdrant retriever."""
    config = get_config()
    
    # Initialize Qdrant client
    client = QdrantClient(
        host=config.qdrant.host,
        port=config.qdrant.port
    )
    
    # Get embeddings
    embeddings = get_langchain_embeddings()
    
    # Create Qdrant vector store
    vector_store = Qdrant(
        client=client,
        collection_name=config.qdrant.collection_name,
        embeddings=embeddings
    )
    
    # Configure retriever based on search type
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
    """Get the Qdrant vector store instance."""
    config = get_config()
    
    # Initialize Qdrant client
    client = QdrantClient(
        host=config.qdrant.host,
        port=config.qdrant.port
    )
    
    # Get embeddings
    embeddings = get_langchain_embeddings()
    
    # Create Qdrant vector store
    vector_store = Qdrant(
        client=client,
        collection_name=config.qdrant.collection_name,
        embeddings=embeddings
    )
    
    return vector_store