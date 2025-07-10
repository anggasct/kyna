from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from kyna.core.db import db_manager
from kyna.core.logging_config import setup_logging
from kyna.api.endpoints import ask, documents, files

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(level="INFO", format_type="detailed")
    db_manager.create_tables()
    yield


app = FastAPI(
    title="Kyna FAQ Assistant",
    description="AI-powered FAQ assistant using RAG pipeline with LangChain",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ask.router, prefix="/api", tags=["ask"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(files.router, prefix="/files", tags=["files"])

@app.get("/")
async def root():
    return {
        "message": "Kyna FAQ Assistant API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}