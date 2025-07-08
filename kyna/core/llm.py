from langchain_community.chat_models import ChatLiteLLM
from langchain_core.language_models import BaseLanguageModel
from .config import get_config

def get_llm() -> BaseLanguageModel:
    """Get the configured LLM instance."""
    config = get_config()
    
    llm = ChatLiteLLM(
        model=config.llm.model,
        temperature=0.1,
        max_tokens=1000,
        timeout=30,
        max_retries=3
    )
    
    return llm

def get_condensing_llm() -> BaseLanguageModel:
    """Get LLM instance for question condensing in conversational mode."""
    return get_llm()