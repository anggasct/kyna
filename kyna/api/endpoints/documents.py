import os
import shutil
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from kyna.core.db import get_db
from kyna.core.document_processor import get_document_processor
from kyna.core.document_manager import get_document_manager
from kyna.core.models import Document as DocumentModel

router = APIRouter()

class DocumentInfo(BaseModel):
    doc_id: int
    filename: str
    document_type: str
    created_at: datetime
    updated_at: datetime

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total: int

class DocumentUploadResponse(BaseModel):
    status: str
    filename: str
    doc_id: str
    message: str

class DocumentDeleteResponse(BaseModel):
    status: str
    doc_id: str
    message: str

class DocumentStatsResponse(BaseModel):
    total_documents: int
    document_types: List[str]

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a new document file for ingestion.
    
    - **file**: The document file to upload (PDF, TXT, etc.)
    
    Returns document ID and processing status.
    """
    try:
        # Validate file type
        allowed_extensions = ['.pdf', '.txt', '.md', '.docx']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Supported types: {', '.join(allowed_extensions)}"
            )
        
        # Create data directory if it doesn't exist
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        
        # Save uploaded file
        file_path = os.path.join(data_dir, file.filename)
        
        # Handle file name conflicts
        counter = 1
        original_path = file_path
        while os.path.exists(file_path):
            name, ext = os.path.splitext(original_path)
            file_path = f"{name}_{counter}{ext}"
            counter += 1
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process document
        doc_processor = get_document_processor()
        doc_id = doc_processor.process_document(file_path, os.path.basename(file_path))
        
        return DocumentUploadResponse(
            status="success",
            filename=os.path.basename(file_path),
            doc_id=doc_id,
            message="Document uploaded and processed successfully"
        )
    
    except Exception as e:
        # Clean up file if processing failed
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading document: {str(e)}"
        )

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(db: Session = Depends(get_db)):
    """
    List all ingested documents.
    
    Returns a list of all documents in the knowledge base with metadata.
    """
    try:
        doc_manager = get_document_manager()
        documents = doc_manager.get_all_documents()
        
        document_list = [
            DocumentInfo(
                doc_id=doc.id,
                filename=doc.filename,
                document_type=doc.document_type,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            )
            for doc in documents
        ]
        
        return DocumentListResponse(
            documents=document_list,
            total=len(document_list)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing documents: {str(e)}"
        )

@router.get("/documents/stats", response_model=DocumentStatsResponse)
async def get_document_stats(db: Session = Depends(get_db)):
    """
    Get document statistics.
    
    Returns statistics about the knowledge base including total documents and document types.
    """
    try:
        doc_manager = get_document_manager()
        stats = doc_manager.get_document_stats()
        
        return DocumentStatsResponse(
            total_documents=stats["total_documents"],
            document_types=stats["document_types"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document stats: {str(e)}"
        )

@router.delete("/documents/{doc_id}", response_model=DocumentDeleteResponse)
async def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Delete a document and its associated vectors from the knowledge base.
    
    - **doc_id**: The ID of the document to delete
    
    This will remove the document from both the database and the vector store.
    """
    try:
        doc_processor = get_document_processor()
        success = doc_processor.delete_document(str(doc_id))
        
        if success:
            return DocumentDeleteResponse(
                status="success",
                doc_id=str(doc_id),
                message="Document deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {doc_id} not found"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )

@router.get("/documents/{doc_id}")
async def get_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Get details for a specific document.
    
    - **doc_id**: The ID of the document to retrieve
    """
    try:
        doc_manager = get_document_manager()
        document = doc_manager.get_document_by_id(doc_id)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {doc_id} not found"
            )
        
        return {
            "doc_id": document.id,
            "filename": document.filename,
            "filepath": document.filepath,
            "document_type": document.document_type,
            "content_hash": document.content_hash,
            "vector_count": len(document.vector_ids),
            "created_at": document.created_at,
            "updated_at": document.updated_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving document: {str(e)}"
        )