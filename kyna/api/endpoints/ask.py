from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from kyna.core.rag_chain import get_rag_chain
from kyna.core.db import get_db
from sqlalchemy.orm import Session

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str = Field(..., description="The user's question")
    session_id: Optional[str] = Field(None, description="Session ID for conversational memory")

class SourceDocument(BaseModel):
    page_content: str
    metadata: Dict[str, Any]

class QuestionResponse(BaseModel):
    question: str
    answer: str
    source_documents: List[SourceDocument]

class SessionHistoryResponse(BaseModel):
    session_id: str
    history: List[Dict[str, str]]

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    try:
        rag_chain = get_rag_chain()
        
        # Get response from RAG chain
        response = rag_chain.ask(
            question=request.question,
            session_id=request.session_id
        )
        
        return QuestionResponse(
            question=response["question"],
            answer=response["answer"],
            source_documents=[
                SourceDocument(
                    page_content=doc["page_content"],
                    metadata=doc["metadata"]
                )
                for doc in response["source_documents"]
            ]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )

@router.get("/sessions/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str):
    try:
        rag_chain = get_rag_chain()
        history = rag_chain.get_session_history(session_id)
        
        return SessionHistoryResponse(
            session_id=session_id,
            history=history
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving session history: {str(e)}"
        )

@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    try:
        rag_chain = get_rag_chain()
        success = rag_chain.clear_session(session_id)
        
        if success:
            return {"message": f"Session {session_id} cleared successfully"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing session: {str(e)}"
        )