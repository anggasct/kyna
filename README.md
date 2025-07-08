# Kyna - AI FAQ Assistant

Kyna is an AI-powered FAQ assistant built using a RAG (Retrieval-Augmented Generation) pipeline with LangChain. The system provides intelligent answers to user questions by combining document retrieval with large language models.

## Features

- **RAG Pipeline**: Combines document retrieval with LLM generation for accurate, contextual answers
- **Conversational Memory**: Maintains context across questions in a conversation session
- **Multiple Embedding Providers**: Supports OpenAI and FastEmbed for document embeddings
- **Flexible LLM Support**: Compatible with various LLM providers via LiteLLM
- **Document Management**: Upload, list, and delete documents via REST API
- **Web Interface**: Streamlit-based playground for easy interaction
- **Vector Storage**: Uses Qdrant for efficient similarity search
- **Configurable**: YAML-based configuration for easy customization

## Architecture

The system follows a modular architecture:

- **Backend**: FastAPI with Python
- **AI Orchestration**: LangChain for RAG pipeline
- **Vector Store**: Qdrant for document embeddings
- **Database**: SQLAlchemy with SQLite (MVP) for metadata
- **UI**: Streamlit playground
- **Configuration**: YAML config files with environment variables

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (or other LLM provider)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd kyna
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Start the application with Docker Compose:
```bash
docker-compose up --build
```

4. Open your browser to:
   - `http://localhost:8501` for the Streamlit playground
   - `http://localhost:8000/docs` for the API documentation

### Manual Installation (Alternative)

If you prefer to run without Docker:

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
alembic upgrade head
```

3. Start Qdrant (using Docker):
```bash
docker run -p 6333:6333 qdrant/qdrant
```

4. Start the FastAPI backend:
```bash
uvicorn kyna.api.main:app --reload
```

5. Start the Streamlit playground:
```bash
streamlit run kyna/playground/app.py
```

## Configuration

The system is configured via `config/config.yaml`:

```yaml
# Database Configuration
database:
  url: "sqlite:///kyna.db"

# Qdrant Vector Store
qdrant:
  host: "localhost"
  port: 6333
  collection_name: "kyna_faq"

# Embedding Configuration
embedding:
  provider: "fastembed"  # or "openai"
  model: "BAAI/bge-small-en-v1.5"

# LLM Configuration
llm:
  model: "gpt-3.5-turbo"

# RAG Settings
rag:
  retriever:
    search_type: "similarity_score_threshold"
    search_k: 4
    score_threshold: 0.7
  prompt_template: "Use the following pieces of context..."

# Memory Settings
memory:
  ttl_seconds: 3600
  max_history_length: 10
```

## API Endpoints

### Ask Question
```bash
POST /api/ask
{
  "question": "What is the return policy?",
  "session_id": "optional-session-id"
}
```

### Document Management
```bash
# Upload document
POST /api/documents/upload
# Form data with file

# List documents
GET /api/documents

# Delete document
DELETE /api/documents/{doc_id}

# Get document details
GET /api/documents/{doc_id}
```

### Session Management
```bash
# Get session history
GET /api/sessions/{session_id}/history

# Clear session
DELETE /api/sessions/{session_id}
```

## Usage Examples

### Basic Question (Stateless)
```python
import requests

response = requests.post("http://localhost:8000/api/ask", json={
    "question": "What are your business hours?"
})
print(response.json()["answer"])
```

### Conversational Question (Stateful)
```python
import requests

# First question
response1 = requests.post("http://localhost:8000/api/ask", json={
    "question": "What is your return policy?",
    "session_id": "user-123"
})

# Follow-up question with context
response2 = requests.post("http://localhost:8000/api/ask", json={
    "question": "How long does it take?",
    "session_id": "user-123"
})
```

### Document Upload
```python
import requests

files = {"file": open("document.pdf", "rb")}
response = requests.post("http://localhost:8000/api/documents/upload", files=files)
print(response.json())
```

## Project Structure

```
kyna/
├── config/
│   └── config.yaml          # Main configuration
├── data/                    # Document storage
├── kyna/
│   ├── api/
│   │   ├── main.py         # FastAPI application
│   │   └── endpoints/
│   │       ├── ask.py      # Question endpoints
│   │       └── documents.py# Document management
│   ├── core/
│   │   ├── config.py       # Configuration loader
│   │   ├── db.py           # Database management
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── embedder.py     # Embedding adapters
│   │   ├── llm.py          # LLM interface
│   │   ├── retriever.py    # Qdrant retriever
│   │   ├── rag_chain.py    # RAG pipeline
│   │   ├── document_processor.py  # Document processing
│   │   └── document_manager.py    # Document metadata
│   └── playground/
│       └── app.py          # Streamlit UI
├── alembic/                # Database migrations
├── requirements.txt
├── .env.example
└── README.md
```

## Development

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

### Adding New Document Types

1. Update the allowed extensions in `documents.py`
2. Add appropriate loader in `document_processor.py`
3. Test with the new document type

### Customizing the RAG Pipeline

1. Modify prompt templates in `config.yaml`
2. Adjust retrieval parameters (k, score_threshold)
3. Change embedding models or LLM providers

## Troubleshooting

### Common Issues

**Qdrant Connection Error**
- Ensure Qdrant is running on the configured host:port
- Check firewall settings

**Import Errors**
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python version compatibility

**Database Issues**
- Run migrations: `alembic upgrade head`
- Check database file permissions

**API Key Errors**
- Verify API keys in `.env` file
- Check LLM provider configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation at `/docs` when running the API
- Review the configuration options in `config.yaml`