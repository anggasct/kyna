# Kyna Project Makefile
# Docker build and management commands

.PHONY: help build build-debug build-prod up up-debug down down-debug clean logs logs-debug restart restart-debug

# Default target
help:
	@echo "Kyna Project - Docker Commands"
	@echo "================================"
	@echo ""
	@echo "Production Commands:"
	@echo "  make build-prod     - Build production containers"
	@echo "  make up-prod        - Start production containers"
	@echo "  make down-prod      - Stop production containers"
	@echo "  make logs-prod      - View production logs"
	@echo "  make restart-prod   - Restart production containers"
	@echo ""
	@echo "Debug Commands:"
	@echo "  make build-debug    - Build debug containers"
	@echo "  make up-debug       - Start debug containers"
	@echo "  make down-debug     - Stop debug containers"
	@echo "  make logs-debug     - View debug logs"
	@echo "  make restart-debug  - Restart debug containers"
	@echo ""
	@echo "General Commands:"
	@echo "  make clean          - Clean all containers and volumes"
	@echo "  make clean-images   - Remove all Kyna images"
	@echo "  make clean-volumes  - Remove all volumes"
	@echo "  make status         - Show container status"
	@echo ""
	@echo "Database Commands:"
	@echo "  make db-reset       - Reset all database data (Qdrant + PostgreSQL)"
	@echo "  make db-reset-prod  - Reset production database data"
	@echo "  make db-reset-debug - Reset debug database data"
	@echo "  make db-backup      - Backup both Qdrant and PostgreSQL databases"
	@echo "  make db-restore     - Restore databases from backup (specify BACKUP_TIMESTAMP=YYYYMMDD_HHMMSS)"
	@echo "  make db-reset-force - Force reset without confirmation (dangerous!)"
	@echo ""
	@echo "Development Commands:"
	@echo "  make init           - Initialize project (migrations, etc.)"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linting"

# =============================================================================
# PRODUCTION BUILDS
# =============================================================================

build-prod:
	@echo "Building production containers..."
	docker-compose build --no-cache

up-prod:
	@echo "Starting production containers..."
	docker-compose up -d
	@echo "Production containers started!"
	@echo "API: http://localhost:8000"
	@echo "Playground: http://localhost:8501"
	@echo "Qdrant: http://localhost:6333"

down-prod:
	@echo "Stopping production containers..."
	docker-compose down

logs-prod:
	@echo "Production logs (Press Ctrl+C to exit)..."
	docker-compose logs -f

restart-prod: down-prod up-prod

# =============================================================================
# DEBUG BUILDS
# =============================================================================

build-debug:
	@echo "Building debug containers..."
	docker-compose -f docker-compose.debug.yml build

up-debug:
	@echo "Starting debug containers..."
	docker-compose -f docker-compose.debug.yml up -d
	@echo "Debug containers started!"
	@echo "API: http://localhost:8000 (Debug: 5678)"
	@echo "Playground: http://localhost:8501 (Debug: 5679)"
	@echo "Qdrant: http://localhost:6333"
	@echo ""
	@echo "To debug in VS Code:"
	@echo "1. Open VS Code"
	@echo "2. Press F5 or go to Run and Debug"
	@echo "3. Select 'Debug Docker API Container' or 'Debug Docker Playground Container'"

down-debug:
	@echo "Stopping debug containers..."
	docker-compose -f docker-compose.debug.yml down

logs-debug:
	@echo "Debug logs (Press Ctrl+C to exit)..."
	docker-compose -f docker-compose.debug.yml logs -f

restart-debug: build-debug up-debug

# =============================================================================
# INDIVIDUAL CONTAINER BUILDS
# =============================================================================

build-api:
	@echo "Building API container..."
	docker build -f Dockerfile.api -t kyna-api:latest .

build-api-debug:
	@echo "Building API debug container..."
	docker build -f Dockerfile.api.debug -t kyna-api:debug .

build-playground:
	@echo "Building Playground container..."
	docker build -f Dockerfile.playground -t kyna-playground:latest .

build-playground-debug:
	@echo "Building Playground debug container..."
	docker build -f Dockerfile.playground.debug -t kyna-playground:debug .

# =============================================================================
# UTILITY COMMANDS
# =============================================================================

status:
	@echo "Container Status:"
	@docker ps -a --filter "name=kyna" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

clean:
	@echo "Cleaning all containers and volumes..."
	docker-compose down -v --remove-orphans
	docker-compose -f docker-compose.debug.yml down -v --remove-orphans
	@echo "Cleanup completed!"

clean-images:
	@echo "Removing Kyna images..."
	docker images | grep kyna | awk '{print $$3}' | xargs -r docker rmi -f
	@echo "Images removed!"

clean-volumes:
	@echo "Removing volumes..."
	docker volume prune -f
	@echo "Volumes removed!"

clean-all: clean clean-images clean-volumes

# =============================================================================
# DATABASE COMMANDS
# =============================================================================

db-reset:
	@echo "Resetting all database data..."
	@echo "This will delete ALL data in Qdrant and PostgreSQL databases!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "Stopping containers..."
	docker-compose down
	docker-compose -f docker-compose.debug.yml down
	@echo "Removing Qdrant data volume..."
	docker volume rm kyna_qdrant_data 2>/dev/null || true
	@echo "Removing PostgreSQL database volume..."
	docker volume rm kyna_postgres_data 2>/dev/null || true
	@echo "Database reset completed!"
	@echo "Run 'make up' or 'make up-debug' to start with fresh database"

db-reset-prod:
	@echo "Resetting production database data..."
	@echo "This will delete ALL data in production Qdrant and SQLite databases!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "Stopping production containers..."
	docker-compose down
	@echo "Removing Qdrant data volume..."
	docker volume rm kyna_qdrant_data 2>/dev/null || true
	@echo "Removing PostgreSQL database volume..."
	docker volume rm kyna_postgres_data 2>/dev/null || true
	@echo "Production database reset completed!"
	@echo "Run 'make up-prod' to start with fresh database"

db-reset-debug:
	@echo "Resetting debug database data..."
	@echo "This will delete ALL data in debug Qdrant and SQLite databases!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "Stopping debug containers..."
	docker-compose -f docker-compose.debug.yml down
	@echo "Removing Qdrant data volume..."
	docker volume rm kyna_qdrant_data 2>/dev/null || true
	@echo "Removing PostgreSQL database volume..."
	docker volume rm kyna_postgres_data 2>/dev/null || true
	@echo "Debug database reset completed!"
	@echo "Run 'make up-debug' to start with fresh database"

db-backup:
	@echo "Creating database backup..."
	@mkdir -p backups
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	echo "Backing up Qdrant database..."; \
	docker run --rm -v kyna_qdrant_data:/source -v $(PWD)/backups:/backup alpine \
		tar czf /backup/qdrant_backup_$$timestamp.tar.gz -C /source . 2>/dev/null || true; \
	echo "Backing up PostgreSQL database..."; \
	docker run --rm -v kyna_postgres_data:/source -v $(PWD)/backups:/backup alpine \
		tar czf /backup/postgres_backup_$$timestamp.tar.gz -C /source . 2>/dev/null || true; \
	echo "PostgreSQL backup created: backups/postgres_backup_$$timestamp.tar.gz"; \
	echo "Qdrant backup created: backups/qdrant_backup_$$timestamp.tar.gz"; \
	echo "Backup completed with timestamp: $$timestamp"

db-restore:
	@echo "Restoring database from backup..."
	@if [ -z "$(BACKUP_TIMESTAMP)" ]; then \
		echo "Please specify backup timestamp: make db-restore BACKUP_TIMESTAMP=20250109_054300"; \
		echo "Available backups:"; \
		ls -la backups/ 2>/dev/null | grep backup || echo "No backups found"; \
		exit 1; \
	fi
	@if [ ! -f "backups/qdrant_backup_$(BACKUP_TIMESTAMP).tar.gz" ] && [ ! -f "backups/postgres_backup_$(BACKUP_TIMESTAMP).tar.gz" ]; then \
		echo "No backup files found for timestamp: $(BACKUP_TIMESTAMP)"; \
		echo "Available backups:"; \
		ls -la backups/ 2>/dev/null | grep backup || echo "No backups found"; \
		exit 1; \
	fi
	@echo "This will replace ALL current database data!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "Stopping containers..."
	docker-compose down
	docker-compose -f docker-compose.debug.yml down
	@echo "Removing current data..."
	docker volume rm kyna_qdrant_data 2>/dev/null || true
	docker volume rm kyna_postgres_data 2>/dev/null || true
	@echo "Restoring from backup..."
	@if [ -f "backups/qdrant_backup_$(BACKUP_TIMESTAMP).tar.gz" ]; then \
		echo "Restoring Qdrant database..."; \
		docker volume create kyna_qdrant_data; \
		docker run --rm -v kyna_qdrant_data:/target -v $(PWD)/backups/qdrant_backup_$(BACKUP_TIMESTAMP).tar.gz:/backup.tar.gz alpine \
			tar xzf /backup.tar.gz -C /target; \
		echo "Qdrant database restored"; \
	fi
	@if [ -f "backups/postgres_backup_$(BACKUP_TIMESTAMP).tar.gz" ]; then \
		echo "Restoring PostgreSQL database..."; \
		docker volume create kyna_postgres_data; \
		docker run --rm -v kyna_postgres_data:/target -v $(PWD)/backups/postgres_backup_$(BACKUP_TIMESTAMP).tar.gz:/backup.tar.gz alpine \
			tar xzf /backup.tar.gz -C /target; \
		echo "PostgreSQL database restored"; \
	fi
	@echo "Database restoration completed!"
	@echo "Run 'make up' or 'make up-debug' to start with restored database"

db-reset-force:
	@echo "Force resetting database data (no confirmation)..."
	docker-compose down 2>/dev/null || true
	docker-compose -f docker-compose.debug.yml down 2>/dev/null || true
	docker volume rm kyna_qdrant_data 2>/dev/null || true
	docker volume rm kyna_postgres_data 2>/dev/null || true
	@echo "Database force reset completed!"

# =============================================================================
# DEVELOPMENT COMMANDS
# =============================================================================

init:
	@echo "Initializing project..."
	@echo "Creating directories..."
	@mkdir -p data
	@echo "Running database migrations..."
	@if [ -f "alembic.ini" ]; then \
		alembic upgrade head; \
	else \
		echo "No alembic.ini found, skipping migrations"; \
	fi
	@echo "Project initialized!"

test:
	@echo "Running tests..."
	@if [ -f "requirements.txt" ] && grep -q "pytest" requirements.txt; then \
		python -m pytest; \
	else \
		echo "No pytest found in requirements.txt"; \
	fi

lint:
	@echo "Running linting..."
	@if [ -f "requirements.txt" ] && grep -q "flake8" requirements.txt; then \
		python -m flake8 kyna/; \
	else \
		echo "No flake8 found in requirements.txt"; \
	fi

# =============================================================================
# QUICK ALIASES
# =============================================================================

# Short aliases for common commands
build: build-prod
up: up-prod
down: down-prod
logs: logs-prod
restart: restart-prod

# Debug aliases
debug: up-debug
stop-debug: down-debug