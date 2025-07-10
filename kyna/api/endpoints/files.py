import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from kyna.core.db import get_db
from kyna.core.document_manager import get_document_manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{doc_id}")
async def serve_file(doc_id: int, db: Session = Depends(get_db)):
    try:
        doc_manager = get_document_manager()
        document = doc_manager.get_document_by_id(doc_id)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {doc_id} not found"
            )
        
        # Only serve files for file-based documents
        if document.source_type != 'file':
            raise HTTPException(
                status_code=400,
                detail="This endpoint only serves uploaded files, not URL-based documents"
            )
        
        # Construct file path (stored files should be in data directory)
        data_dir = "data"
        file_path = os.path.join(data_dir, document.filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="File not found on disk"
            )
        
        return FileResponse(
            path=file_path,
            filename=document.filename,
            media_type='application/octet-stream'
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error serving file: {str(e)}"
        )