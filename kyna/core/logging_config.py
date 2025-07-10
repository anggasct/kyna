"""
Logging Configuration Module - Sets up application-wide logging.

This module provides a centralized function to configure Python's logging
system, allowing for different logging levels and formats. It also
adjusts logging levels for external libraries to reduce noise.

Key components:
- `setup_logging`: Configures the root logger and specific loggers.
- `get_rag_logger`: Provides a specific logger for RAG chain operations.

Integration:
- Called during application startup (e.g., in `api/main.py`).
- Loggers are used throughout the core modules for debugging and monitoring.
"""
import logging
import sys
from typing import Optional

def setup_logging(level: str = "INFO", format_type: str = "detailed") -> None:
    formats = {
        "simple": "%(levelname)s - %(name)s - %(message)s",
        "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=formats.get(format_type, formats["detailed"]),
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )
    
    rag_logger = logging.getLogger("kyna.core.rag_chain")
    rag_logger.setLevel(logging.INFO)
    
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("litellm").setLevel(logging.WARNING)

def get_rag_logger() -> logging.Logger:
    return logging.getLogger("kyna.core.rag_chain")