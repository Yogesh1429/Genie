import logging
from typing import Optional
# from langchain.memory import ConversationBufferMemory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.language_models import BaseChatModel
from genie.agent.config.agent_config import AgentConfig
from typing import Optional
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.language_models import BaseChatModel
from langchain_community.chat_message_histories import ChatMessageHistory
from genie.agent.config.agent_config import AgentConfig

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Memory manager for Genie: wraps a ChatMessageHistory instead of ConversationBufferMemory
    to align with new LangChain style and give full control over trimming and token usage.
    """

    def __init__(self, config: AgentConfig, llm: Optional[BaseChatModel] = None):
        self.config = config
        self.llm = llm  # LLM instance for accurate token counting
        self.chat_memory = ChatMessageHistory()
        self.memory = self
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count without external downloads.
        Uses word/character-based heuristics that work well across all providers.
        """
        if not text:
            return 0
            
        # Fallback to word-based calculation
        words = len(text.split())
        chars = len(text)
        estimated = int(words * 1.3 + chars * 0.01)
        return max(1, estimated)
    
    def _total_tokens(self) -> int:
        # CHANGED: Previously iterated over self.memory.chat_memory.messages (ConversationBufferMemory);
        # now we read directly from self.chat_memory.messages because we removed the wrapper.
        total = 0
        for msg in self.chat_memory.messages:
            content = getattr(msg, "content", "")
            total += self._estimate_tokens(str(content))
        return total
    
    def trim_if_needed(self) -> None:
        messages = self.chat_memory.messages
        # Token-based trimming loop; keep at least one user+AI turn 
        while self._total_tokens() > self.config.max_tokens_in_memory and len(messages) > 2:
            removed = messages.pop(0)
            logger.info(f"Trimmed message (token limit), removed ~{self._estimate_tokens(getattr(removed, 'content', ''))} tokens")

    def check_memory_status(self) -> None:
        if self._total_tokens() > self.config.max_tokens_in_memory:
            logger.info(f"Memory is full, total tokens: {self._total_tokens()}")
        else:
            logger.info(f"Memory is not full, total tokens: {self._total_tokens()}")

    def clear(self) -> None:
        # CHANGED: Previously called self.memory.clear() on ConversationBufferMemory;
        # now we clear the underlying ChatMessageHistory directly.
        self.chat_memory.clear()
        logger.info("Memory cleared")
    
    def set_llm(self, llm: Optional[BaseChatModel]) -> None:
        """Update the LLM instance for token counting"""
        self.llm = llm
        logger.info(f"LLM instance updated for token counting: {type(llm).__name__ if llm else 'None'}")

    # NOTE (migration):
    # - Removed _create_memory, _recreate_memory, and reset_memory, which were only needed
    #   to rebuild ConversationBufferMemory with memory_key/output_key. ChatMessageHistory
    #   does not require those wrappers, so we manage history directly.

