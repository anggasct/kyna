"""
LLM Module - Provides an interface for interacting with Large Language Models.

This module wraps the LiteLLM library to provide a consistent way to
communicate with various LLM providers. It integrates with LangChain
to allow LLMs to be used within RAG pipelines.

Key components:
- `LiteLLMWrapper`: A custom LangChain LLM class that uses LiteLLM.

Integration:
- Used by `rag_chain` to generate answers and condense questions.
- Uses `config` for LLM model settings.
"""
from langchain_core.language_models import BaseLanguageModel
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks import CallbackManagerForLLMRun
from typing import Any, List, Optional
import litellm
from .config import get_config

class LiteLLMWrapper(LLM):
    """LangChain wrapper for LiteLLM."""
    
    model: str
    temperature: float = 0.1
    max_tokens: int = 1000
    timeout: int = 30
    max_retries: int = 3
    
    @property
    def _llm_type(self) -> str:
        return "litellm"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = litellm.completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
                max_retries=self.max_retries,
                stop=stop,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ValueError(f"LiteLLM call failed: {str(e)}")

def get_llm() -> BaseLanguageModel:
    return LiteLLMWrapper(
        model=get_config().llm.model,
        temperature=0.1,
        max_tokens=1000,
        timeout=30,
        max_retries=3
    )

def get_condensing_llm() -> BaseLanguageModel:
    return get_llm()