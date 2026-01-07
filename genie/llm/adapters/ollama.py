from typing import Any, Dict, Optional
import logging

try:
	from langchain_ollama import ChatOllama  # preferred
except Exception:
	try:
		from langchain_community.chat_models import ChatOllama  # fallback
	except Exception:
		ChatOllama = None

logger = logging.getLogger('genie.llm.adapters.ollama')  


def build(cfg: Dict[str, Any], model: Optional[str] = None):
	logger.info(f"Building Ollama LLM with model: {model}")
	model = model or (cfg.get("model") or "").strip() or None
	base_url = (cfg.get("base_url") or cfg.get("endpoint") or "").strip() or None
	
	logger.debug(f"Ollama config - model: {model}, base_url: {base_url}")
	
	if ChatOllama is None:
		logger.error("Ollama dependencies not available")
		raise ImportError("Ollama adapter requires 'langchain-ollama' or community ChatOllama installed.")
	
	logger.info(f"Successfully created Ollama ChatLLM instance for model {model}")
	return ChatOllama(model=model, base_url=base_url)





