from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from kyna.core.db import db_manager
from kyna.api.endpoints import ask, documents

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler."""
    # Startup
    db_manager.create_tables()
    yield
    # Shutdown

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
app.include_router(documents.router, prefix="/api", tags=["documents"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Kyna FAQ Assistant API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}