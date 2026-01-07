from typing import Any, Dict, Optional
import logging

from langchain_anthropic import ChatAnthropic

logger = logging.getLogger('genie.llm.adapters.anthropic')


def build(cfg: Dict[str, Any], model: Optional[str] = None):
	logger.info(f"Building Anthropic LLM with model: {model}")
	model = model or (cfg.get("model") or "").strip() or None
	api_key = (cfg.get("api_key") or "").strip() or None
	
	logger.debug(f"Anthropic config - model: {model}, api_key: {'***' if api_key else 'None'}")
	
	if ChatAnthropic is None:
		logger.error("langchain_anthropic not available")
		raise ImportError("Anthropic adapter requires langchain_anthropic.")
	
	if not api_key:
		logger.error("Anthropic API key is missing")
		raise ValueError("Anthropic api_key is required (store in profile or set ANTHROPIC_API_KEY).")
	
	logger.info("Successfully created Anthropic ChatLLM instance")
	return ChatAnthropic(model=model, api_key=api_key)





