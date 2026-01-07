from typing import Any, Dict, List

from ..core.secure_storage import SecureStorage


def list_registry_profiles() -> List[Dict[str, Any]]:

	ss = SecureStorage()
	return ss.get_all_profiles()

def list_registry_profile_names() -> List[Dict[str, str]]:

	ss = SecureStorage()
	return ss.list_profiles()



