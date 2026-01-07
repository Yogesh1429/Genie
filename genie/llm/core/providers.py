import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger('genie.llm.core.providers')

def load_providers(providers_path: Path) -> Tuple[Dict[str, List[str]], Dict[str, str], Dict[str, str]]:
	logger.info(f"Loading providers from: {providers_path}")
	name_to_endpoint: Dict[str, str] = {}
	name_to_id: Dict[str, str] = {}
	try:
		if providers_path.exists():
			logger.debug("Providers file found, parsing JSON")
			data = json.loads(providers_path.read_text(encoding="utf-8"))
			if isinstance(data, list):
				mapped: Dict[str, List[str]] = {}
				for item in data:
					name = item.get("name")
					pid = item.get("id") or (name.lower() if name else None)
					models = item.get("models", [])
					endpoint = item.get("baseUrl") or item.get("base_url") or ""
					if pid != 'qcli' and name and isinstance(models, list):
						mapped[name] = models
						name_to_endpoint[name] = endpoint
						if pid:
							name_to_id[name] = pid
							logger.debug(f"Loaded provider: {name} with {len(models)} models")
					else:
						logger.info(f"Skipping provider: {name} with pid: {pid} and models: {models}")
				if mapped:
					logger.info(f"Successfully loaded {len(mapped)} providers")
					return mapped, name_to_endpoint, name_to_id
		else:
			logger.warning(f"Providers file not found: {providers_path}")
	except Exception as e:
		logger.error(f"Failed to load providers: {e}")
		return {}, {}, {}