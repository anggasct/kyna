import os
import hashlib
from typing import List, Dict, Any
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, UnstructuredFileLoader
from langchain.schema import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from .config import get_config
from .embedder import get_embedding_adapter
from .models import Document as DocumentModel
from .db import get_db

class DocumentProcessor:
    """Handles document processing, chunking, and embedding."""
    
    def __init__(self):
        self.config = get_config()
        self.embedding_adapter = get_embedding_adapter()
        self.qdrant_client = QdrantClient(
            host=self.config.qdrant.host,
            port=self.config.qdrant.port
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.ingestion.chunk_size,
            chunk_overlap=self.config.ingestion.chunk_overlap,
            length_function=len,
        )
    
    def _ensure_collection_exists(self):
        """Ensure Qdrant collection exists."""
        collections = self.qdrant_client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if self.config.qdrant.collection_name not in collection_names:
            self.qdrant_client.create_collection(
                collection_name=self.config.qdrant.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate hash for file content."""
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash
    
    def _load_document(self, file_path: str) -> List[Document]:
        """Load document using appropriate loader."""
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
        else:
            loader = UnstructuredFileLoader(file_path)
        
        return loader.load()
    
    def _chunk_document(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        return self.text_splitter.split_documents(documents)
    
    def _embed_chunks(self, chunks: List[Document]) -> List[List[float]]:
        """Generate embeddings for document chunks."""
        texts = [chunk.page_content for chunk in chunks]
        return self.embedding_adapter.embed_documents(texts)
    
    def _store_vectors(self, chunks: List[Document], embeddings: List[List[float]], doc_id: str) -> List[str]:
        """Store vectors in Qdrant and return vector IDs."""
        self._ensure_collection_exists()
        
        points = []
        vector_ids = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_id = f"{doc_id}_{i}"
            vector_ids.append(vector_id)
            
            point = PointStruct(
                id=vector_id,
                vector=embedding,
                payload={
                    "content": chunk.page_content,
                    "metadata": chunk.metadata,
                    "document_id": doc_id
                }
            )
            points.append(point)
        
        self.qdrant_client.upsert(
            collection_name=self.config.qdrant.collection_name,
            points=points
        )
        
        return vector_ids
    
    def process_document(self, file_path: str, filename: str) -> str:
        """Process a document and store it in the knowledge base."""
        # Generate content hash
        content_hash = self._get_file_hash(file_path)
        
        # Check if document already exists
        db = next(get_db())
        existing_doc = db.query(DocumentModel).filter(
            DocumentModel.content_hash == content_hash
        ).first()
        
        if existing_doc:
            return existing_doc.id
        
        # Load and process document
        documents = self._load_document(file_path)
        chunks = self._chunk_document(documents)
        embeddings = self._embed_chunks(chunks)
        
        # Create document record
        doc_model = DocumentModel(
            filename=filename,
            filepath=file_path,
            document_type=Path(file_path).suffix.lower(),
            content_hash=content_hash,
            vector_ids=[]  # Will be updated after storing vectors
        )
        
        db.add(doc_model)
        db.commit()
        db.refresh(doc_model)
        
        # Store vectors
        vector_ids = self._store_vectors(chunks, embeddings, str(doc_model.id))
        
        # Update document with vector IDs
        doc_model.vector_ids = vector_ids
        db.commit()
        
        return str(doc_model.id)
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and its associated vectors."""
        db = next(get_db())
        doc_model = db.query(DocumentModel).filter(
            DocumentModel.id == doc_id
        ).first()
        
        if not doc_model:
            return False
        
        # Delete vectors from Qdrant
        if doc_model.vector_ids:
            self.qdrant_client.delete(
                collection_name=self.config.qdrant.collection_name,
                points_selector=doc_model.vector_ids
            )
        
        # Delete file if it exists
        if os.path.exists(doc_model.filepath):
            os.remove(doc_model.filepath)
        
        # Delete database record
        db.delete(doc_model)
        db.commit()
        
        return True

def get_document_processor() -> DocumentProcessor:
    """Get document processor instance."""
    return DocumentProcessor()