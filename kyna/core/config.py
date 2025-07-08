import os
import yaml
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

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
    """Load configuration from YAML file."""
    with open(config_path, 'r') as file:
        yaml_content = file.read()
    
    # Simple environment variable substitution
    import re
    
    # Replace ${VAR_NAME:default_value} with environment variable value or default
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
    """Get singleton configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config