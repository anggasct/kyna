import os
import shutil
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from kyna.core.db import get_db
from kyna.core.document_processor import get_document_processor
from kyna.core.document_manager import get_document_manager
from kyna.core.models import Document as DocumentModel

logger = logging.getLogger(__name__)

router = APIRouter()

class DocumentInfo(BaseModel):
    doc_id: int
    filename: str
    source_type: str
    source_url: str
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
    source_url: str

class DocumentDeleteResponse(BaseModel):
    status: str
    doc_id: str
    message: str

class DocumentStatsResponse(BaseModel):
    total_documents: int
    document_types: List[str]
    source_types: List[str]
    file_documents: int
    url_documents: int

class DocumentUrlRequest(BaseModel):
    url: str = Field(..., description="URL to extract content from")
    filename: str = Field(None, description="Optional custom filename")

class DocumentUrlResponse(BaseModel):
    status: str
    filename: str
    doc_id: str
    message: str
    source_url: str

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
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
        
        # Get the created document to return details
        doc_manager = get_document_manager()
        document = doc_manager.get_document_by_id(int(doc_id))
        
        logger.info(f"Document processed successfully: {file_path}, doc_id: {doc_id} (type: {type(doc_id)})")
        
        return DocumentUploadResponse(
            status="success",
            filename=os.path.basename(file_path),
            doc_id=str(doc_id),
            message="Document uploaded and processed successfully",
            source_url=document.source_url if document else f"/files/{doc_id}"
        )
    
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        
        # Clean up file if processing failed
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading document: {str(e)}"
        )

@router.post("/add-url", response_model=DocumentUrlResponse)
async def add_url_document(
    request: DocumentUrlRequest,
    db: Session = Depends(get_db)
):
    try:
        # Process URL document
        doc_processor = get_document_processor()
        doc_id = doc_processor.process_url(request.url, request.filename)
        
        # Get the created document to return details
        doc_manager = get_document_manager()
        document = doc_manager.get_document_by_id(int(doc_id))
        
        if not document:
            raise HTTPException(
                status_code=500,
                detail="Document was processed but could not be retrieved"
            )
        
        logger.info(f"URL document processed successfully: {request.url}, doc_id: {doc_id}")
        
        return DocumentUrlResponse(
            status="success",
            filename=document.filename,
            doc_id=str(doc_id),
            message="URL document processed successfully",
            source_url=document.source_url
        )
    
    except Exception as e:
        logger.error(f"Error processing URL document: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing URL document: {str(e)}"
        )

@router.get("", response_model=DocumentListResponse)
async def list_documents(db: Session = Depends(get_db)):
    try:
        doc_manager = get_document_manager()
        documents = doc_manager.get_all_documents()
        
        document_list = [
            DocumentInfo(
                doc_id=doc.id,
                filename=doc.filename,
                source_type=doc.source_type,
                source_url=doc.source_url,
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

@router.get("/stats", response_model=DocumentStatsResponse)
async def get_document_stats(db: Session = Depends(get_db)):
    try:
        doc_manager = get_document_manager()
        stats = doc_manager.get_document_stats()
        
        return DocumentStatsResponse(
            total_documents=stats["total_documents"],
            document_types=stats["document_types"],
            source_types=stats["source_types"],
            file_documents=stats["file_documents"],
            url_documents=stats["url_documents"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document stats: {str(e)}"
        )

@router.delete("/{doc_id}", response_model=DocumentDeleteResponse)
async def delete_document(doc_id: int, db: Session = Depends(get_db)):
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

@router.get("/{doc_id}")
async def get_document(doc_id: int, db: Session = Depends(get_db)):
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
            "source_type": document.source_type,
            "source_url": document.source_url,
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

@router.post("/clear-all")
async def clear_all_documents():
    try:
        doc_processor = get_document_processor()
        success = doc_processor.clear_all_documents()
        
        if success:
            return {
                "status": "success",
                "message": "All documents cleared successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to clear all documents"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing all documents: {str(e)}"
        )

