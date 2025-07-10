# Kyna - AI Knowledge Assistant

**K**now **Y**our **N**ext **A**nswer

Kyna is an AI-powered knowledge assistant built using a RAG (Retrieval-Augmented Generation) pipeline with LangChain. The system provides intelligent answers to user questions by retrieving relevant information from your knowledge base and combining it with large language models.

## Features

- **RAG Pipeline**: Combines document retrieval with LLM generation for accurate, contextual answers
- **Conversational Memory**: Maintains context across questions in a conversation session
- **Multiple Embedding Providers**: Supports OpenAI and FastEmbed for document embeddings
- **Flexible LLM Support**: Compatible with various LLM providers via LiteLLM
- **Document Management**: Upload, list, and delete documents via REST API
- **Web Interface**: Streamlit-based playground for easy interaction
- **Vector Storage**: Uses Qdrant for efficient similarity search
- **Configurable**: YAML-based configuration for easy customization
- **Docker Support**: Full containerization with production and debug modes
- **Database Management**: Comprehensive backup and restore capabilities

## Architecture

The system follows a modular architecture:

- **Backend**: FastAPI with Python
- **AI Orchestration**: LangChain for RAG pipeline
- **Vector Store**: Qdrant for document embeddings
- **Database**: SQLAlchemy with SQLite (MVP) for metadata
- **UI**: Streamlit playground
- **Configuration**: YAML config files with environment variables
- **Containerization**: Docker with production and debug configurations

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

3. Start the application:
```bash
# Build and start production containers
make build
make up

# Or use Docker Compose directly
docker-compose up --build
```

4. Open your browser to:
   - `http://localhost:8501` for the Streamlit playground
   - `http://localhost:8000/docs` for the API documentation
   - `http://localhost:6333/dashboard` for the Qdrant dashboard

### Debug Mode

For development with debugging support:

```bash
# Build and start debug containers
make build-debug
make up-debug

# Or use Docker Compose directly
docker-compose -f docker-compose.debug.yml up --build
```

Debug ports:
- API Debug: `localhost:5678`
- Playground Debug: `localhost:5679`

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

# Qdrant Vector Store Configuration
qdrant:
  host: "${QDRANT_HOST:localhost}"
  port: ${QDRANT_PORT:6333}
  collection_name: "kyna_faq"

# Embedding Model Configuration
embedding:
  provider: "fastembed"  # or "openai"
  model: "BAAI/bge-small-en-v1.5"

# LLM Provider Configuration (using LiteLLM)
llm:
  model: "gpt-3.5-turbo"  # or "openrouter/google/gemini-pro", "groq/llama3-70b-8192"

# Data Ingestion Configuration
ingestion:
  chunk_size: 1200
  chunk_overlap: 200

# RAG Chain Configuration
rag:
  retriever:
    search_type: "similarity"  # or "similarity_score_threshold"
    search_k: 10
    score_threshold: 0.2
  prompt_template: "config/prompts/prompt.md"

# Conversational Memory Configuration
memory:
  ttl_seconds: 3600
  max_history_length: 10
```

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Required: OpenAI API Key
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Other LLM Provider Keys
OPENROUTER_API_KEY=sk-or-your-openrouter-api-key-here
GROQ_API_KEY=your-groq-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Optional: Qdrant Cloud Configuration
QDRANT_URL=https://your-qdrant-instance.com
QDRANT_API_KEY=your-qdrant-api-key-here
```

## Makefile Commands

The project includes a comprehensive Makefile for Docker management:

### Production Commands

```bash
make help           # Show all available commands
make build          # Build production containers
make up             # Start production containers
make down           # Stop production containers
make logs           # View production logs
make restart        # Restart production containers
```

### Debug Commands

```bash
make build-debug    # Build debug containers
make up-debug       # Start debug containers
make down-debug     # Stop debug containers
make logs-debug     # View debug logs
make restart-debug  # Restart debug containers
```

### Database Management

```bash
make db-reset       # Reset all database data (with confirmation)
make db-backup      # Backup Qdrant and SQLite databases
make db-restore     # Restore from backup (specify BACKUP_TIMESTAMP)
make db-reset-force # Force reset without confirmation
```

### Utility Commands

```bash
make status         # Show container status
make clean          # Clean containers and volumes
make clean-images   # Remove all Kyna images
make clean-volumes  # Remove all volumes
make init           # Initialize project
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
```


## Project Structure

```
kyna/
├── config/
│   ├── config.yaml          # Main configuration
│   └── prompts/
│       └── prompt.md        # RAG prompt template
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
│   │   ├── document_manager.py    # Document metadata
│   │   └── logging_config.py      # Logging configuration
│   └── playground/
│       └── app.py          # Streamlit UI
├── alembic/                # Database migrations
├── docker-compose.yml      # Production Docker setup
├── docker-compose.debug.yml # Debug Docker setup
├── Dockerfile.api          # API container
├── Dockerfile.playground   # Playground container
├── Makefile               # Docker management commands
├── requirements.txt
├── .env.example
└── README.md
```

## Development

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Adding New Document Types

1. Update the allowed extensions in `kyna/api/endpoints/documents.py`
2. Add appropriate loader in `kyna/core/document_processor.py`
3. Test with the new document type

### Customizing the RAG Pipeline

1. Modify prompt templates in `config/prompts/prompt.md`
2. Adjust retrieval parameters in `config/config.yaml`
3. Change embedding models or LLM providers in configuration

## Troubleshooting

### Common Issues

**Qdrant Connection Error**
- Ensure Qdrant container is running: `make status`
- Check Docker network connectivity
- Verify Qdrant configuration in `config/config.yaml`

**Container Issues**
- Reset all containers: `make clean && make build && make up`
- Check container logs: `make logs`
- Verify Docker and Docker Compose installation

**Database Issues**
- Reset database: `make db-reset`
- Check database permissions
- Verify Alembic migrations

**API Key Errors**
- Verify API keys in `.env` file
- Check LLM provider configuration in `config/config.yaml`
- Ensure environment variables are loaded correctly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes with `make build && make up`
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the API documentation at `http://localhost:8000/docs`
- Review the configuration options in `config/config.yaml`
- Use `make help` to see all available commands