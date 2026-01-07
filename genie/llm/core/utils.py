from typing import Any, Dict, List, Optional


def first(items: List[Dict[str, Any]], pred) -> Optional[Dict[str, Any]]:

	for it in items:
		try:
			if pred(it):
				return it
		except Exception:
			pass
	return None


































