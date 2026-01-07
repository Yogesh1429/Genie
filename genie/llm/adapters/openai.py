from typing import Any, Dict, Optional
import logging

from langchain_openai import ChatOpenAI

logger = logging.getLogger('genie.llm.adapters.openai')


def build(cfg: Dict[str, Any], model: Optional[str] = None):
	logger.info(f"Building OpenAI LLM with model: {model}")
	model = model or (cfg.get("model") or "").strip() or None
	base_url = (cfg.get("base_url") or cfg.get("endpoint") or "").strip() or None
	api_key = (cfg.get("api_key") or "").strip() or None
	
	logger.debug(f"OpenAI config - model: {model}, base_url: {base_url}, api_key: {'***' if api_key else 'None'}")
	
	if ChatOpenAI is None:
		logger.error("langchain_openai not available")
		raise ImportError("OpenAI adapter requires langchain_openai.")
	
	kwargs: Dict[str, Any] = {"model": model, "api_key": api_key}
	if base_url:
		kwargs["base_url"] = base_url
	
	logger.info("Successfully created OpenAI ChatLLM instance")
	return ChatOpenAI(**kwargs)





