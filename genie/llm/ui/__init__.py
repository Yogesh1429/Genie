from typing import TYPE_CHECKING

__all__ = ["LLMProviderSelector"]

if TYPE_CHECKING:
	from .selector import LLMProviderSelector as LLMProviderSelector  # for type checkers only


def __getattr__(name: str):
	if name == "LLMProviderSelector":
		from .selector import LLMProviderSelector as _LLMProviderSelector
		return _LLMProviderSelector
	raise AttributeError(f"module 'genie.llm.ui' has no attribute {name!r}")

