from typing import Any, Dict, Optional, List
import logging

from ..profiles.registry import list_registry_profiles
from ..core.utils import first
from .build_llm import build_chat_llm

logger = logging.getLogger('genie.llm.factory.retrieve_llm')


def create_llm_from_registry(profile_name: Optional[str] = None, model: Optional[str] = None):
	'''1. Retrieves the LLM configs stored in registry
	   2. identifies the required config
	   3. calls build_chat_llm to build LLM object and returns
	'''
	logger.info(f"Creating LLM from registry - profile: {profile_name}, model: {model}")
	profiles: List[Dict[str, Any]] = list_registry_profiles()
	logger.debug(f"Found {len(profiles)} profiles in registry")
	if not profiles:
		logger.error("No LLM profiles found in registry")
		raise RuntimeError("LLM is not configured. Configure with your LLM Manager.")

	selected: Optional[Dict[str, Any]] = None
	if profile_name:
		name = (profile_name or "").strip().lower()
		logger.debug(f"Searching for profile: {name}")
		selected = first(profiles, lambda p: (p.get("profile_name") or "").strip().lower() == name)

	if not selected:
		logger.info("No specific profile found, using first available profile")
		selected = profiles[0]

	logger.info(f"Selected profile: {selected.get('profile_name', 'unknown')} with provider: {selected.get('provider_id', 'unknown')}")
	return build_chat_llm(selected["provider_id"], selected, model)



