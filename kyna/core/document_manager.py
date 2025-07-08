from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import Document as DocumentModel
from .db import get_db

class DocumentManager:
    """Manages document metadata in the database."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_document(self, filename: str, filepath: str, document_type: str, 
                       content_hash: str, vector_ids: List[str]) -> DocumentModel:
        """Create a new document record."""
        document = DocumentModel(
            filename=filename,
            filepath=filepath,
            document_type=document_type,
            content_hash=content_hash,
            vector_ids=vector_ids
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def get_document_by_id(self, doc_id: int) -> Optional[DocumentModel]:
        """Get document by ID."""
        return self.db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    
    def get_document_by_hash(self, content_hash: str) -> Optional[DocumentModel]:
        """Get document by content hash."""
        return self.db.query(DocumentModel).filter(
            DocumentModel.content_hash == content_hash
        ).first()
    
    def get_all_documents(self) -> List[DocumentModel]:
        """Get all documents."""
        return self.db.query(DocumentModel).all()
    
    def update_document_vector_ids(self, doc_id: int, vector_ids: List[str]) -> bool:
        """Update document vector IDs."""
        document = self.get_document_by_id(doc_id)
        if document:
            document.vector_ids = vector_ids
            self.db.commit()
            return True
        return False
    
    def delete_document(self, doc_id: int) -> bool:
        """Delete document by ID."""
        document = self.get_document_by_id(doc_id)
        if document:
            self.db.delete(document)
            self.db.commit()
            return True
        return False
    
    def document_exists(self, content_hash: str) -> bool:
        """Check if document with given hash exists."""
        return self.get_document_by_hash(content_hash) is not None
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get document statistics."""
        total_docs = self.db.query(DocumentModel).count()
        doc_types = self.db.query(DocumentModel.document_type).distinct().all()
        doc_types = [dtype[0] for dtype in doc_types]
        
        return {
            "total_documents": total_docs,
            "document_types": doc_types
        }

def get_document_manager() -> DocumentManager:
    """Get document manager instance."""
    db = next(get_db())
    return DocumentManager(db)