import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger('genie.llm.core.config_loader')

class ConfigLoader:
    def __init__(self, config_file: str = "config/app_config.json"):
        self.config_file = Path(config_file)
        self._config = None
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load application configuration from external config file"""
        logger.info(f"Loading configuration from: {self.config_file}")
        
        if not self.config_file.exists():
            logger.warning(f"Config file not found: {self.config_file}, using defaults")
            # self._config = self._get_default_config()
            return self._config
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            logger.info("Configuration loaded successfully")
            return self._config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            # self._config = self._get_default_config()
            return None
    
    # def _get_default_config(self) -> Dict[str, Any]:
    #     """Return default configuration"""
    #     return {
    #         "providers_file": "genie/llm/ui/providers.json",  # fallback to old location
    #         "log_level": "INFO",
    #         "app_settings": {
    #             "default_host": "0.0.0.0",
    #             "default_port": 8000
    #         }
    #     }
    
    def get_providers_file_path(self) -> Path:
        """Get the path to providers.json file"""
        # providers_file = self._config.get("providers_file", "config/providers.json")
        # path = Path(providers_file)
        path = self.config_file
        
        logger.debug(f"Providers file path: {path}")
        return path
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self._config.get(key, default)
    
    def get_app_setting(self, key: str, default: Any = None) -> Any:
        """Get app setting value by key"""
        return self._config.get("app_settings", {}).get(key, default)