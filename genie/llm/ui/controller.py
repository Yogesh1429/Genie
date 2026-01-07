from typing import Any, Dict, List, Tuple, Optional
from pathlib import Path

from ...llm.core import SecureStorage, load_providers, test_api


class Controller:
	def __init__(self, encryption_key: Optional[str] = None, config_loader=None):
		self.secure = SecureStorage(custom_key=encryption_key)
		# Use external config loader to get providers.json path
		if config_loader:
			providers_path = config_loader.get_providers_file_path()

		self.providers, self.name_to_endpoint, self.name_to_id = load_providers(providers_path)

	def list_profiles(self) -> List[Dict[str, Any]]:
		return self.secure.get_all_profiles()

	def save_config(self, cfg: Dict[str, Any]) -> bool:
		name = (cfg.get("provider_id") or "").strip()
		return bool(name) and self.secure.save_profile(name, cfg)

	def load_config(self, name: str) -> Optional[Dict[str, Any]]:
		return self.secure.load_profile(name)

	def delete_config(self, name: str) -> bool:
		return self.secure.delete_profile(name)

	def move_config(self, name: str, delta: int) -> bool:
		try:
			return self.secure.move_profile(name, delta)
		except AttributeError:
			return False

	def probe_api(self, provider: str, endpoint: str, api_key: str, ak: str, sk: str) -> Tuple[bool, str]:
		if not provider or not endpoint:
			return False, "Provider and endpoint are required"
		try:
			return test_api(provider, endpoint, api_key, ak, sk)
		except Exception as e:
			return False, f"API test failed: {str(e)}"

























