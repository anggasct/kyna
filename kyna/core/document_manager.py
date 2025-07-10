"""
Document Manager Module - Manages document metadata in the database.

This module provides an interface for interacting with the document metadata
stored in the relational database. It handles CRUD operations for document
records and provides document statistics.

Key components:
- `DocumentManager`: Class for managing document records.

Integration:
- Used by `api/endpoints/documents.py` to list, retrieve, and manage documents.
- Uses `db` for database session management and `models` for document schema.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import Document as DocumentModel
from .db import get_db

class DocumentManager:
    """Manages document metadata in the database."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_document(self, filename: str, source_type: str, source_url: str, 
                       document_type: str, content_hash: str, vector_ids: List[str]) -> DocumentModel:
        document = DocumentModel(
            filename=filename,
            source_type=source_type,
            source_url=source_url,
            document_type=document_type,
            content_hash=content_hash,
            vector_ids=vector_ids
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def get_document_by_id(self, doc_id: int) -> Optional[DocumentModel]:
        return self.db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    
    def get_document_by_hash(self, content_hash: str) -> Optional[DocumentModel]:
        return self.db.query(DocumentModel).filter(
            DocumentModel.content_hash == content_hash
        ).first()
    
    def get_all_documents(self) -> List[DocumentModel]:
        return self.db.query(DocumentModel).all()
    
    def update_document_vector_ids(self, doc_id: int, vector_ids: List[str]) -> bool:
        document = self.get_document_by_id(doc_id)
        if document:
            document.vector_ids = vector_ids
            self.db.commit()
            return True
        return False
    
    def delete_document(self, doc_id: int) -> bool:
        document = self.get_document_by_id(doc_id)
        if document:
            self.db.delete(document)
            self.db.commit()
            return True
        return False
    
    def document_exists(self, content_hash: str) -> bool:
        return self.get_document_by_hash(content_hash) is not None
    
    def get_document_stats(self) -> Dict[str, Any]:
        total_docs = self.db.query(DocumentModel).count()
        doc_types = self.db.query(DocumentModel.document_type).distinct().all()
        doc_types = [dtype[0] for dtype in doc_types]
        
        source_types = self.db.query(DocumentModel.source_type).distinct().all()
        source_types = [stype[0] for stype in source_types]
        
        file_count = self.db.query(DocumentModel).filter(DocumentModel.source_type == 'file').count()
        url_count = self.db.query(DocumentModel).filter(DocumentModel.source_type == 'url').count()
        
        return {
            "total_documents": total_docs,
            "document_types": doc_types,
            "source_types": source_types,
            "file_documents": file_count,
            "url_documents": url_count
        }

def get_document_manager() -> DocumentManager:
    db = next(get_db())
    return DocumentManager(db)