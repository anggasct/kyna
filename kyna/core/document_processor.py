"""
Document Processing Module - Handles loading, chunking, and embedding of documents.

This module is responsible for preparing raw documents for ingestion into the
knowledge base. It includes logic for:
- Loading various document types (PDF, Markdown, TXT).
- Intelligent chunking, including special handling for FAQ-formatted content.
- Generating vector embeddings for document chunks.
- Storing document metadata and vectors in Qdrant and the relational database.

Integration:
- Uses `config` for ingestion parameters and Qdrant connection details.
- Interacts with `embedder` to generate embeddings.
- Utilizes `db` and `models` for database operations and schema.
"""
import os
import hashlib
import logging
from typing import List, Dict, Any
from pathlib import Path
import uuid
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
from langchain_community.document_loaders import PyPDFLoader
from langchain_unstructured import UnstructuredLoader
from langchain.schema import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from .config import get_config
from .embedder import get_embedding_adapter
from .models import Document as DocumentModel
from .db import get_db
from .web_extractor import get_web_content_extractor

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Manages the end-to-end processing of documents."""
    
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
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.config.qdrant.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.config.qdrant.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {str(e)}", exc_info=True)
            raise
    
    def _get_file_hash(self, file_path: str) -> str:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash
    
    def _get_url_hash(self, url: str) -> str:
        """Generate a hash for URL content."""
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def _extract_filename_from_url(self, url: str) -> str:
        """Extract a reasonable filename from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if path and not path.endswith('/'):
            filename = path.split('/')[-1]
            if '.' in filename:
                return filename
        
        # Use domain name if no good filename found
        domain = parsed.netloc.replace('www.', '')
        return f"{domain}.html"
    
    def _load_url_document(self, url: str) -> List[Document]:
        """Load document content from URL."""
        web_extractor = get_web_content_extractor()
        document = web_extractor.extract_content(url)
        
        if document:
            return [document]
        else:
            return []
    
    def _load_document(self, file_path: str) -> List[Document]:
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
            return loader.load()
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Preserve FAQ structure if detected
            if self._is_faq_content(content):
                return [Document(page_content=content, metadata={"source": file_path})]
            else:
                loader = UnstructuredLoader(file_path)
                return loader.load()
    
    def _chunk_document(self, documents: List[Document]) -> List[Document]:
        chunks = []
        
        full_content = "\n\n".join([doc.page_content for doc in documents])
        is_faq_document = self._is_faq_content(full_content)
        
        if is_faq_document:
            # Use FAQ-specific chunking to keep Q&A pairs together
            for doc in documents:
                chunks.extend(self._split_faq_content(doc))
        else:
            for doc in documents:
                chunks.extend(self.text_splitter.split_documents([doc]))
        
        return chunks
    
    def _is_faq_content(self, content: str) -> bool:
        """
        Determines if the content is likely in an FAQ format.
        
        This method uses a heuristic approach based on common FAQ patterns
        like explicit keywords, Q&A prefixes, and markdown header structures
        to identify FAQ documents.
        """
        structural_patterns = [
            r'FAQ',
            r'Frequently Asked Questions',
            r'Q\s*\d*\s*[:.]',
            r'Question\s*\d*\s*[:.]',
            r'A\s*\d*\s*[:.]',
            r'Answer\s*\d*\s*[:.]',
        ]
        
        question_headers = len(re.findall(r'^##\s*.*\?', content, re.MULTILINE))
        question_marks = content.count('?')
        qa_pattern_matches = len(re.findall(r'##.*\?\s*\n+[^#]', content, re.DOTALL))
        
        score = 0
        
        for pattern in structural_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                score += 3
        
        if question_headers >= 2:
            score += question_headers
        
        if question_marks >= 3:
            score += 1
        
        if qa_pattern_matches >= 2:
            score += qa_pattern_matches * 2
        
        return score >= 3
    
    def _split_faq_content(self, document: Document) -> List[Document]:
        """
        Splits FAQ content into chunks, attempting to keep Q&A pairs intact.
        
        This custom splitting logic prioritizes keeping a question and its
        corresponding answer within the same chunk, even if it exceeds
        the standard chunk size, to maintain conversational context.
        """
        content = document.page_content
        chunks = []
        
        sections = re.split(r'\n(?=##\s+)', content)
        
        for section in sections:
            if not section.strip():
                continue
            
            section = section.strip()
            
            lines = [line.strip() for line in section.split('\n') if line.strip()]
            if len(lines) < 2:
                continue
            
            max_faq_chunk_size = self.config.ingestion.chunk_size * 2
            
            if len(section) > max_faq_chunk_size:
                paragraphs = re.split(r'\n\n+', section)
                current_chunk = ""
                
                for paragraph in paragraphs:
                    test_chunk = current_chunk + ("\n\n" if current_chunk else "") + paragraph
                    
                    if len(test_chunk) <= max_faq_chunk_size:
                        current_chunk = test_chunk
                    else:
                        if current_chunk:
                            question_line = lines[0] if lines[0].startswith('##') else ""
                            chunk_with_context = question_line + "\n\n" + current_chunk if question_line and not current_chunk.startswith('##') else current_chunk
                            
                            chunks.append(Document(
                                page_content=chunk_with_context,
                                metadata=document.metadata.copy()
                            ))
                        current_chunk = paragraph
                
                if current_chunk:
                    question_line = lines[0] if lines[0].startswith('##') else ""
                    chunk_with_context = question_line + "\n\n" + current_chunk if question_line and not current_chunk.startswith('##') else current_chunk
                    
                    chunks.append(Document(
                        page_content=chunk_with_context,
                        metadata=document.metadata.copy()
                    ))
            else:
                chunk_doc = Document(
                    page_content=section,
                    metadata=document.metadata.copy()
                )
                chunks.append(chunk_doc)
        
        return chunks
    
    def _embed_chunks(self, chunks: List[Document]) -> List[List[float]]:
        try:
            texts = [chunk.page_content for chunk in chunks]
            embeddings = self.embedding_adapter.embed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}", exc_info=True)
            raise
    
    def _store_vectors(self, chunks: List[Document], embeddings: List[List[float]], doc_id: str) -> List[str]:
        try:
            self._ensure_collection_exists()
            
            points = []
            vector_ids = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = str(uuid.uuid4())
                vector_ids.append(vector_id)
                
                point = PointStruct(
                    id=vector_id,
                    vector=embedding,
                    payload={
                        "page_content": chunk.page_content,
                        "metadata": chunk.metadata,
                        "document_id": doc_id,
                        "chunk_index": i
                    }
                )
                points.append(point)
            
            result = self.qdrant_client.upsert(
                collection_name=self.config.qdrant.collection_name,
                points=points
            )
            
            return vector_ids
            
        except Exception as e:
            logger.error(f"Error storing vectors in Qdrant: {str(e)}", exc_info=True)
            raise
    
    def process_document(self, file_path: str, filename: str) -> str:
        """Process a file-based document."""
        return self._process_document(file_path, filename, 'file')
    
    def process_url(self, url: str, filename: str = None) -> str:
        """Process a URL-based document."""
        if not filename:
            filename = self._extract_filename_from_url(url)
        return self._process_document(url, filename, 'url')
    
    def _process_document(self, source: str, filename: str, source_type: str) -> str:
        try:
            db = next(get_db())
            
            # Load document based on source type
            if source_type == 'file':
                content_hash = self._get_file_hash(source)
                source_url = f"/files/placeholder"  # Will be updated after doc creation
                documents = self._load_document(source)
                document_type = Path(source).suffix.lower()
            else:  # URL
                content_hash = self._get_url_hash(source)
                source_url = source
                documents = self._load_url_document(source)
                document_type = 'html'
            
            # Check if document already exists
            existing_doc = db.query(DocumentModel).filter(
                DocumentModel.content_hash == content_hash
            ).first()
            
            if existing_doc:
                return str(existing_doc.id)
            
            if not documents:
                raise ValueError(f"Failed to load content from {source}")
            
            chunks = self._chunk_document(documents)
            embeddings = self._embed_chunks(chunks)
            
            doc_model = DocumentModel(
                filename=filename,
                source_type=source_type,
                source_url=source_url,
                document_type=document_type,
                content_hash=content_hash,
                vector_ids=[]
            )
            
            db.add(doc_model)
            db.commit()
            db.refresh(doc_model)
            
            # Update source_url for file uploads with actual document ID
            if source_type == 'file':
                doc_model.source_url = f"/files/{doc_model.id}"
                db.commit()
            
            vector_ids = self._store_vectors(chunks, embeddings, str(doc_model.id))
            
            doc_model.vector_ids = vector_ids
            db.commit()
            
            return str(doc_model.id)
            
        except Exception as e:
            logger.error(f"Error processing {source_type} {filename}: {str(e)}", exc_info=True)
            raise
    
    def delete_document(self, doc_id: str) -> bool:
        try:
            db = next(get_db())
            doc_model = db.query(DocumentModel).filter(
                DocumentModel.id == doc_id
            ).first()
            
            if not doc_model:
                return False
            
            if doc_model.vector_ids:
                self.qdrant_client.delete(
                    collection_name=self.config.qdrant.collection_name,
                    points_selector=doc_model.vector_ids
                )
            
            # Only remove file for file-based documents
            if doc_model.source_type == 'file' and hasattr(doc_model, 'filepath') and doc_model.filepath and os.path.exists(doc_model.filepath):
                os.remove(doc_model.filepath)
            
            db.delete(doc_model)
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {str(e)}", exc_info=True)
            return False

    def clear_all_documents(self) -> bool:
        try:
            db = next(get_db())
            
            all_docs = db.query(DocumentModel).all()
            
            try:
                self.qdrant_client.delete_collection(self.config.qdrant.collection_name)
                self._ensure_collection_exists()
            except Exception as e:
                logger.error(f"Error clearing Qdrant collection: {str(e)}")
            
            for doc in all_docs:
                if doc.source_type == 'file' and hasattr(doc, 'filepath') and doc.filepath and os.path.exists(doc.filepath):
                    os.remove(doc.filepath)
            
            db.query(DocumentModel).delete()
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing all documents: {str(e)}", exc_info=True)
            return False

def get_document_processor() -> DocumentProcessor:
    return DocumentProcessor()