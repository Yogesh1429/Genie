import json, os, platform, base64
import logging
from pathlib import Path
from typing import Dict, List
from cryptography.fernet import Fernet

try:
	import winreg  # type: ignore
except Exception:
	winreg = None  # type: ignore

from .crypto import derive_key_from_password, dpapi_protect, dpapi_unprotect

logger = logging.getLogger('genie.llm.core.secure_storage')

APP_NAME = "LLMProviderSelector"
REGISTRY_KEY = r"SOFTWARE\TPF Software\zTPFGI\GenIE\LLMProviderManager"
ENTROPY = "GenIE"
CONFIG_KEY = "api_configs"
ENCRYPTION_KEY = "encryption_key"
class SecureStorage:
	def __init__(self, custom_key: str | None = None):
		logger.info("Initializing SecureStorage")
		self.app_name = APP_NAME
		self.registry_key = REGISTRY_KEY
		self.custom_key = self._load_key_from_config() or custom_key
		logger.info(f"SecureStorage initialized with {'custom key' if self.custom_key else 'system key'}")

	def _load_key_from_config(self) -> str | None:
		env_key = os.getenv("LLM_PROVIDER_ENCRYPTION_KEY")
		if env_key:
			logger.info("Using encryption key from environment variable")
			return env_key
		config_path = Path("encryption_config.json")
		if config_path.exists():
			logger.info("Loading encryption key from config file")
			with open(config_path, "r", encoding="utf-8") as file:
				config = json.load(file)
				return config.get(ENCRYPTION_KEY)
		logger.info("No custom encryption key found")
		return None

	def _get_encryption_key(self) -> bytes:
		if self.custom_key:
			return derive_key_from_password(self.custom_key)

		key_data: bytes | None = None
		if platform.system() == "Windows" and winreg is not None:
			try:
				with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_READ) as reg_key:
					encrypted_key = winreg.QueryValueEx(reg_key, ENCRYPTION_KEY)[0]
				if encrypted_key:
					key_data = dpapi_unprotect(encrypted_key, ENTROPY)
			except Exception as e:
				print(e)
				pass

		if not key_data:
			key_data = Fernet.generate_key()
			self._store_encryption_key(key_data)
		return key_data

	# Backwards-compat shims (in case anything calls these privately)
	# def _protect_dpapi(self, data: bytes, machine_scope=False, entropy: str | None = None) -> bytes | None:
	# 	return dpapi_protect(data, machine_scope, entropy)

	# def _unprotect_dpapi(self, blob: bytes, entropy: str | None = None) -> bytes | None:
	# 	return dpapi_unprotect(blob, entropy)
	
	def _store_encryption_key(self, key_data: bytes) -> bool:
		if self.custom_key:
			return True
		if platform.system() == "Windows" and winreg is not None:
			try:
				encrypted_key = dpapi_protect(key_data, False, ENTROPY)
				if not encrypted_key:
					return False
				with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_WRITE) as reg_key:
					winreg.SetValueEx(reg_key, ENCRYPTION_KEY, 0, winreg.REG_BINARY, encrypted_key)
				return True
			except Exception as e:
				print(e)
				pass
		return False

	def _encrypt_data(self, data: Dict) -> str | None:
		try:
			key = self._get_encryption_key()
			result = base64.b64encode(Fernet(key).encrypt(json.dumps(data).encode())).decode()
			logger.debug("Data encrypted successfully")
			return result
		except Exception as e:
			logger.error(f"Failed to encrypt data: {e}")
			return None

	def _decrypt_data(self, encrypted_data: str) -> Dict | None:
		try:
			key = self._get_encryption_key()
			result = json.loads(Fernet(key).decrypt(base64.b64decode(encrypted_data.encode())).decode())
			logger.debug("Data decrypted successfully")
			return result
		except Exception as e:
			logger.error(f"Failed to decrypt data: {e}")
			return None

	# ----- Multi-profile support -----
	def _read_multi_payload(self) -> Dict:
		payload: Dict = {"version": 1, "profiles": []}
		enc: str | None = None
		if platform.system() == "Windows" and winreg is not None:
			try:
				with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_READ) as reg_key:
					enc = winreg.QueryValueEx(reg_key, CONFIG_KEY)[0]
			except Exception as e:
				print(e)
				pass

		if enc:
			dec = self._decrypt_data(enc)
			if isinstance(dec, dict) and "profiles" in dec:
				return dec
		return payload

	def _write_multi_payload(self, payload: Dict) -> bool:
		enc = self._encrypt_data(payload)
		if not enc:
			return False
		if platform.system() == "Windows" and winreg is not None:
			try:
				with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_WRITE) as reg_key:
					winreg.SetValueEx(reg_key, CONFIG_KEY, 0, winreg.REG_SZ, enc)
				return True
			except Exception as e:
				print(e)
				pass
		return False

	def list_profiles(self) -> List[Dict[str, str]]:
		profiles: List[Dict[str, str]] = []
		payload = self._read_multi_payload()

		for p in payload.get("profiles", []) :
			if p.get("name") and p.get("config", {}).get("model"):
				profiles.append({"name": p.get("name", ""), "model": p.get("config", {}).get("model", "")})

		return profiles

	def get_all_profiles(self) -> List[Dict]:
		payload = self._read_multi_payload()
		out: List[Dict] = []
		for p in payload.get("profiles", []):
			cfg = p.get("config") or {}
			name = p.get("name") or ""
			if name and isinstance(cfg, dict):
				cfg2 = dict(cfg)
				cfg2.setdefault("provider_id", cfg2.get("provider") or name)
				cfg2["profile_name"] = name
				out.append(cfg2)
		return out

	def save_profile(self, name: str, config: Dict) -> bool:
		if not name:
			logger.warning("Attempted to save profile with empty name")
			return False
		logger.info(f"Saving profile: {name}")
		payload = self._read_multi_payload()
		profiles = payload.setdefault("profiles", [])
		key = (config.get("provider_id") or name)
		for p in profiles:
			if p.get("name") == key:
				logger.info(f"Updating existing profile: {key}")
				p["config"] = config
				return self._write_multi_payload(payload)
		logger.info(f"Creating new profile: {key}")
		profiles.append({"name": key, "config": config})
		return self._write_multi_payload(payload)

	def load_profile(self, name: str) -> Dict | None:
		if not name:
			logger.warning("Attempted to load profile with empty name")
			return None
		logger.info(f"Loading profile: {name}")
		payload = self._read_multi_payload()
		for p in payload.get("profiles", []):
			if p.get("name") == name:
				cfg = p.get("config")
				if isinstance(cfg, dict):
					logger.info(f"Successfully loaded profile: {name}")
					return cfg
		logger.warning(f"Profile not found: {name}")
		return None

	def delete_profile(self, name: str) -> bool:
		if not name:
			logger.warning("Attempted to delete profile with empty name")
			return False
		logger.info(f"Deleting profile: {name}")
		payload = self._read_multi_payload()
		before = len(payload.get("profiles", []))
		payload["profiles"] = [p for p in payload.get("profiles", []) if p.get("name") != name]
		if len(payload["profiles"]) == before:
			logger.warning(f"Profile not found for deletion: {name}")
			return False
		logger.info(f"Profile deleted successfully: {name}")
		ok = self._write_multi_payload(payload)
		try:
			if ok and platform.system() == "Windows" and winreg is not None:
				with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_ALL_ACCESS) as reg_key:
					if not payload.get("profiles", []):
						try:
							winreg.DeleteValue(reg_key, CONFIG_KEY)
						except Exception as e:
							print(e)
							pass
		except Exception as e:
			print(e)
			pass
		return ok

	def move_profile(self, name: str, delta: int) -> bool:
		payload = self._read_multi_payload()
		profiles = payload.get("profiles", [])
		idx = -1
		for i, p in enumerate(profiles):
			if p.get("name") == name:
				idx = i
				break
			cfg = p.get("config") or {}
			if (cfg.get("provider_id") or cfg.get("provider")) == name:
				idx = i
				break
		if idx < 0:
			return False
		new_idx = max(0, min(len(profiles) - 1, idx + int(delta)))
		if new_idx == idx:
			return False
		item = profiles.pop(idx)
		profiles.insert(new_idx, item)
		logger.info(f"Profile moved. Old: {idx}, New: {new_idx}, Name: {name}, Delta: {delta}")
		return self._write_multi_payload(payload)