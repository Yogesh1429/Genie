"""Utility functions for loading application configuration from a file.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional
logger = logging.getLogger(__name__)
'''
{
  "providers_file": "C:/Users/Deepa/Desktop/providers.json",
  "log_path": "C:/Users/Deepa/Desktop/logs",
  "log_level": "DEBUG",
  "log_retention_days":10,
  "mcp": {
		"ztpfgi_help": {
			"transport": "streamable_http",
			"url": "http://localhost:8500/mcp"
		}
  }
}

MCP Configuration for Kiro CLI as per latest docs:
To Do: Test this with and without /mcp in the url
"mcp": {
		"ztpfgi_help": {
			"type": "http",
			"url": "http://localhost:8500/mcp"
		}
  }


'''
def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load the application configuration JSON into a dictionary.
    """
    candidate = path or os.getenv("APP_CONFIG_FILE")
    if candidate:
        config_path = Path(candidate).expanduser()
        if config_path.is_absolute():
            with config_path.open("r", encoding="utf-8") as f:
                config = json.load(f)
                
                # Log only keys (not values)
                logger.info(f"Config keys loaded: {list(config.keys())}")
                return config
        
    raise FileNotFoundError(f"No configuration file found at {candidate}")

def get_log_level(config: Optional[Mapping[str, Any]] = None, default: int = logging.INFO) -> int:
    """Extract the logging level from config and return the logging level"""
    
    if config is None:
        config = load_config()  

    value = config.get("log_level")
    if value is None:
        return default

    return value

def get_log_path(config: Optional[Mapping[str, Any]] = None) -> str:
    """Extract the logging path from config and return the logging path"""
    
    if config is None:
        config = load_config()

    value = config.get("log_path")
    # if value is None:
    #     raise ValueError("log_path is not set in the config")

    return value

def get_providers_file() -> str:
    """Extract the providers file from config and return the providers file"""
    value = os.getenv("PROVIDERS_FILE")
    if value:
        if not os.path.exists(value):
            raise FileNotFoundError(f"Providers file not found: {value}")
        logger.info(f"Providers file from env: {value}")
        return value
    raise ValueError("providers_file is not set in PROVIDERS_FILE env var")

def get_mcp(config: Optional[Mapping[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
	if config is None:
		config = load_config()

	value = config.get("mcp")
	# if value is None:
	# 	raise ValueError("mcp is not set in the config")

	return value

def get_log_retention_days(config: Optional[Mapping[str, Any]] = None) -> int:
	if config is None:
		config = load_config()

	value = config.get("log_retention_days")
	if value is None:
		return 30

	return value
    
def get_qcli_default_model(config: Optional[Mapping[str, Any]] = None) -> str:
    """Get the first QCLI model from providers file"""
    try:
        providers_file = get_providers_file()
        with open(providers_file, 'r', encoding='utf-8') as f:
            providers = json.load(f)
        
        for provider in providers:
            if provider.get("id") == "qcli":
                models = provider.get("models", [])
                logger.info(f"Default Model: {models[0]}")
                return models[0] if models else "claude-sonnet-4"
    except Exception as e:
        logger.error(f"Failed to load QCLI default model: {e}")
    
    return "claude-sonnet-4"

def get_max_tokens_in_memory(config: Optional[Mapping[str, Any]] = None) -> int:
	if config is None:
		config = load_config()

	value = config.get("max_tokens_in_memory")
	if value is None:
		return 4000
	logger.info(f"Max tokens in memory from config: {value}")
	return value

def get_chat_history_path() -> str:
    """Extract the chat history path from config and return the chat history path"""
    chat_history_path = os.getenv("GENIE_CHAT_HISTORY_PATH")
    if chat_history_path:
        return chat_history_path
    return "none"

def get_identity_provider(config: Optional[Mapping[str, Any]] = None) -> str:
    """Extract the identity provider from config and return the identity provider"""
    if config is None:
        config = load_config()
 
    value = config.get("identity_provider")
    if value is None:
        raise ValueError("identity_provider is not set in the config")
    return value
 
def get_region(config: Optional[Mapping[str, Any]] = None) -> str:
    """Extract the region from config and return the region"""
    if config is None:
        config = load_config()
 
    value = config.get("region")
    if value is None:
        raise ValueError("region is not set in the config")
    return value