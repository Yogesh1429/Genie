from typing import Any, Dict, Optional
import logging

from ..adapters import openai as openai_adapter
from ..adapters import anthropic as anthropic_adapter
from ..adapters import ollama as ollama_adapter
from ..adapters import bedrock as bedrock_adapter
# from ..adapters import watsonx as watsonx_adapter  

logger = logging.getLogger('genie.llm.factory.build_llm')

PROVIDERS = {
	"openai": openai_adapter.build,
	"anthropic": anthropic_adapter.build,
	"ollama": ollama_adapter.build,
	"aws-bedrock": bedrock_adapter.build,
    # "ibm-watsonx": watsonx_adapter.build
}

def build_chat_llm(provider_id: str, cfg: Dict[str, Any], model: Optional[str] = None):
	'''1. Based on the provider_id, calls the corresponding Adapter
	   2. returns respective Chat LLM object 
	'''
	logger.info(f"Building LLM for provider: {provider_id}, model: {model}")
	builder = PROVIDERS.get(provider_id)
	if not builder:
		logger.error(f"Unsupported provider: {provider_id}")
		raise ValueError(f"Unsupported provider in adapter: {provider_id}")
	
	logger.debug(f"Using adapter for {provider_id}")
	llm = builder(cfg, model)
	logger.info(f"Successfully built LLM for {provider_id}")
	return llm
