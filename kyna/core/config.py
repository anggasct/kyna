"""
Configuration Module - Manages application settings and environment variables.

This module is responsible for loading and providing access to the application's
configuration, which is defined in a YAML file and can be augmented with
environment variables. It uses dataclasses for type-safe configuration access.

Key components:
- Various dataclasses (`DatabaseConfig`, `QdrantConfig`, etc.) to define the
  structure of the configuration.
- `load_config`: Function to load the configuration from a YAML file.
- `get_config`: Provides a singleton instance of the loaded configuration.

Integration:
- Used by almost all other core modules to access application settings.
"""
import os
import yaml
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
import re

load_dotenv()

@dataclass
class DatabaseConfig:
    url: str

@dataclass
class QdrantConfig:
    host: str
    port: int
    collection_name: str

@dataclass
class EmbeddingConfig:
    provider: str
    model: str

@dataclass
class LLMConfig:
    model: str

@dataclass
class IngestionConfig:
    chunk_size: int
    chunk_overlap: int

@dataclass
class RetrieverConfig:
    search_type: str
    search_k: int
    score_threshold: float

@dataclass
class RAGConfig:
    retriever: RetrieverConfig
    prompt_template: str

@dataclass
class MemoryConfig:
    ttl_seconds: int
    max_history_length: int

@dataclass
class Config:
    database: DatabaseConfig
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    llm: LLMConfig
    ingestion: IngestionConfig
    rag: RAGConfig
    memory: MemoryConfig

def load_config(config_path: str = "config/config.yaml") -> Config:
    with open(config_path, 'r') as file:
        yaml_content = file.read()
    
    def replace_env_var(match):
        var_name = match.group(1)
        default_value = match.group(2) if match.group(2) else ""
        return os.getenv(var_name, default_value)
    
    yaml_content = re.sub(r'\$\{([^:}]+):([^}]*)\}', replace_env_var, yaml_content)
    config_data = yaml.safe_load(yaml_content)
    
    return Config(
        database=DatabaseConfig(**config_data['database']),
        qdrant=QdrantConfig(**config_data['qdrant']),
        embedding=EmbeddingConfig(**config_data['embedding']),
        llm=LLMConfig(**config_data['llm']),
        ingestion=IngestionConfig(**config_data['ingestion']),
        rag=RAGConfig(
            retriever=RetrieverConfig(**config_data['rag']['retriever']),
            prompt_template=config_data['rag']['prompt_template']
        ),
        memory=MemoryConfig(**config_data['memory'])
    )

_config: Optional[Config] = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = load_config()
    return _config