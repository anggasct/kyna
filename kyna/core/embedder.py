"""
Embedding Module - Provides an abstraction layer for different embedding models.

This module defines an `EmbeddingAdapter` interface and concrete implementations
for various embedding providers (e.g., OpenAI, FastEmbed). It ensures that
the rest of the application can interact with embedding models uniformly,
regardless of the underlying provider.

Key components:
- `EmbeddingAdapter`: Abstract base class for embedding operations.
- `OpenAIEmbeddingAdapter`: Concrete implementation for OpenAI embeddings.
- `FastEmbedAdapter`: Concrete implementation for FastEmbed (local) embeddings.

Integration:
- Used by `document_processor` to generate embeddings for document chunks.
- Used by `retriever` to get LangChain-compatible embedding instances.
"""
import logging
from abc import ABC, abstractmethod
from typing import List
from .config import get_config

logger = logging.getLogger(__name__)

_embedding_adapters = {}
_langchain_embeddings = {}

class EmbeddingAdapter(ABC):
    """Abstract base class for embedding adapters."""
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass
    
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass

class OpenAIEmbeddingAdapter(EmbeddingAdapter):
    def __init__(self, model: str = "text-embedding-3-small"):
        from langchain_openai import OpenAIEmbeddings
        self.embeddings = OpenAIEmbeddings(model=model)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)

class FastEmbedAdapter(EmbeddingAdapter):
    def __init__(self, model: str = "BAAI/bge-small-en-v1.5"):
        from langchain_community.embeddings import FastEmbedEmbeddings
        self.embeddings = FastEmbedEmbeddings(model_name=model)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)

class SentenceTransformersAdapter(EmbeddingAdapter):
    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(model_name=model)
        except ImportError:
            raise ImportError(
                "Sentence Transformers dependencies not installed. "
                "Please install: pip install sentence-transformers transformers torch langchain-huggingface"
            )
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)

def get_embedding_adapter() -> EmbeddingAdapter:
    config = get_config()
    cache_key = f"{config.embedding.provider}:{config.embedding.model}"
    
    if cache_key not in _embedding_adapters:
        if config.embedding.provider == "openai":
            _embedding_adapters[cache_key] = OpenAIEmbeddingAdapter(model=config.embedding.model)
        elif config.embedding.provider == "fastembed":
            _embedding_adapters[cache_key] = FastEmbedAdapter(model=config.embedding.model)
        elif config.embedding.provider == "sentence_transformers":
            _embedding_adapters[cache_key] = SentenceTransformersAdapter(model=config.embedding.model)
        else:
            raise ValueError(f"Unsupported embedding provider: {config.embedding.provider}")
    
    return _embedding_adapters[cache_key]

def get_langchain_embeddings():
    config = get_config()
    cache_key = f"{config.embedding.provider}:{config.embedding.model}"
    
    if cache_key not in _langchain_embeddings:
        if config.embedding.provider == "openai":
            from langchain_openai import OpenAIEmbeddings
            _langchain_embeddings[cache_key] = OpenAIEmbeddings(model=config.embedding.model)
        elif config.embedding.provider == "fastembed":
            from langchain_community.embeddings import FastEmbedEmbeddings
            _langchain_embeddings[cache_key] = FastEmbedEmbeddings(model_name=config.embedding.model)
        elif config.embedding.provider == "sentence_transformers":
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
                _langchain_embeddings[cache_key] = HuggingFaceEmbeddings(model_name=config.embedding.model)
            except ImportError:
                raise ImportError(
                    "Sentence Transformers dependencies not installed. "
                    "Please install: pip install sentence-transformers transformers torch langchain-huggingface"
                )
        else:
            raise ValueError(f"Unsupported embedding provider: {config.embedding.provider}")
    
    return _langchain_embeddings[cache_key]