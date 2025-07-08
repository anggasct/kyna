# Migration Notes for Package Updates

## Overview
This document outlines the changes made to update packages from 2024 to 2025 versions.

## Package Version Updates

### Major Updates
- **LangChain**: 0.1.20 → 0.3.26 (Breaking changes)
- **OpenAI**: 1.35.14 → 1.91.0 (API improvements)
- **FastAPI**: 0.104.1 → 0.116.0 (Performance improvements)

### All Updates
```
fastapi: 0.104.1 → 0.116.0
uvicorn: 0.24.0 → 0.32.0
langchain: 0.1.20 → 0.3.26
langchain-core: (new) → 0.3.34
langchain-community: 0.0.38 → 0.3.27
langchain-openai: (new) → 0.3.2
qdrant-client: 1.8.2 → 1.14.2
openai: 1.35.14 → 1.91.0
litellm: 1.40.19 → 1.73.0
fastembed: 0.2.7 → 0.3.6
sqlalchemy: 2.0.21 → 2.0.41
alembic: 1.12.1 → 1.16.2
streamlit: 1.28.1 → 1.44.0
```

## Code Changes Required

### 1. LangChain 0.3.x Breaking Changes

**File**: `kyna/core/rag_chain.py`

**Changes Made**:
```python
# OLD imports
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.schema import BaseMessage, HumanMessage, AIMessage

# NEW imports
from langchain_core.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
```

**Reason**: LangChain 0.3.x moved core functionality to `langchain_core` package.

### 2. New Dependencies Added

**File**: `requirements.txt`

**Added**:
- `langchain-core==0.3.34`
- `langchain-openai==0.3.2`

**Reason**: Required for LangChain 0.3.x modular architecture.

## Files That Did NOT Need Changes

- `kyna/core/llm.py` - Already using compatible imports
- `kyna/core/embedder.py` - Already using `langchain_openai`
- `kyna/core/retriever.py` - Already using `langchain_community`
- `kyna/api/main.py` - FastAPI usage is backward compatible

## Testing Recommendations

After updating:

1. **Test imports**:
```bash
python3 -c "from kyna.core.rag_chain import get_rag_chain; print('✓ RAG chain import successful')"
```

2. **Test Docker build**:
```bash
docker-compose build
```

3. **Test functionality**:
```bash
docker-compose up -d
# Test API endpoints
curl http://localhost:8000/health
```

## Potential Issues

1. **LangChain Memory**: If using advanced memory features, check compatibility
2. **OpenAI Client**: Some advanced features might have new parameters
3. **FastAPI**: Dependency injection might behave slightly differently

## Rollback Plan

If issues occur, revert to previous versions:
```bash
git checkout HEAD~1 requirements.txt
git checkout HEAD~1 kyna/core/rag_chain.py
```

## Benefits of Update

- **Performance**: All packages have performance improvements
- **Security**: Latest versions include security fixes
- **Features**: Access to latest LangChain 0.3.x features
- **Compatibility**: Better compatibility with modern Python versions