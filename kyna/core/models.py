"""
Database Models Module - Defines the SQLAlchemy ORM models for the application.

This module contains the data models that map to the relational database schema.
It uses SQLAlchemy's declarative base to define tables and their columns.

Key components:
- `Document`: Represents a document stored in the knowledge base.

Integration:
- Used by `db` to create tables and manage sessions.
- Used by `document_processor` and `document_manager` for data persistence.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Boolean
from sqlalchemy.sql import func
from .db import Base

class Document(Base):
    """Represents a document stored in the knowledge base."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # 'file' or 'url'
    source_url = Column(String, nullable=False)  # URL to access the document
    document_type = Column(String, nullable=False)
    content_hash = Column(String, nullable=False, unique=True)
    vector_ids = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', type='{self.document_type}', source='{self.source_type}')>"
