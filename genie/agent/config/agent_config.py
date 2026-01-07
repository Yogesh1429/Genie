from dataclasses import dataclass
import os

@dataclass
class AgentConfig:
    """Configuration for the agent"""
    profile_name: str = ""
    model_name: str = ""
    max_iterations: int = 6
    temperature: float = 0.2
    verbose: bool = True
    # memory_window: int = 10 # Number of conversation turns (user+AI pairs) to remember
    max_tokens_in_memory: int = None # token budget for retained chat history

    def __post_init__(self):
        if self.max_tokens_in_memory is None:
            self.max_tokens_in_memory = int(os.getenv("MAX_TOKENS_IN_MEMORY", "4000"))