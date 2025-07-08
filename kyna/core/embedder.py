from abc import ABC, abstractmethod
from typing import List
from .config import get_config

# Global cache for embedding adapters
_embedding_adapters = {}
_langchain_embeddings = {}

class EmbeddingAdapter(ABC):
    """Abstract base class for embedding adapters."""
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        pass
    
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a query string."""
        pass

class OpenAIEmbeddingAdapter(EmbeddingAdapter):
    """OpenAI embedding adapter."""
    
    def __init__(self, model: str = "text-embedding-3-small"):
        from langchain_openai import OpenAIEmbeddings
        self.embeddings = OpenAIEmbeddings(model=model)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)

class FastEmbedAdapter(EmbeddingAdapter):
    """FastEmbed embedding adapter."""
    
    def __init__(self, model: str = "BAAI/bge-small-en-v1.5"):
        from langchain_community.embeddings import FastEmbedEmbeddings
        self.embeddings = FastEmbedEmbeddings(model_name=model)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)

def get_embedding_adapter() -> EmbeddingAdapter:
    """Get the configured embedding adapter (cached)."""
    config = get_config()
    cache_key = f"{config.embedding.provider}:{config.embedding.model}"
    
    if cache_key not in _embedding_adapters:
        if config.embedding.provider == "openai":
            _embedding_adapters[cache_key] = OpenAIEmbeddingAdapter(model=config.embedding.model)
        elif config.embedding.provider == "fastembed":
            _embedding_adapters[cache_key] = FastEmbedAdapter(model=config.embedding.model)
        else:
            raise ValueError(f"Unsupported embedding provider: {config.embedding.provider}")
    
    return _embedding_adapters[cache_key]

def get_langchain_embeddings():
    """Get LangChain embeddings instance for use with retrievers (cached)."""
    config = get_config()
    cache_key = f"{config.embedding.provider}:{config.embedding.model}"
    
    if cache_key not in _langchain_embeddings:
        if config.embedding.provider == "openai":
            from langchain_openai import OpenAIEmbeddings
            _langchain_embeddings[cache_key] = OpenAIEmbeddings(model=config.embedding.model)
        elif config.embedding.provider == "fastembed":
            from langchain_community.embeddings import FastEmbedEmbeddings
            _langchain_embeddings[cache_key] = FastEmbedEmbeddings(model_name=config.embedding.model)
        else:
            raise ValueError(f"Unsupported embedding provider: {config.embedding.provider}")
    
    return _langchain_embeddings[cache_key]