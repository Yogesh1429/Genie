import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage
# from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.prompts.chat import ChatPromptTemplate
from fastapi import HTTPException


from ...llm.factory.retrieve_llm import create_llm_from_registry
from ...llm.profiles.registry import list_registry_profile_names
from ..config.agent_config import AgentConfig
from .memory_manager import MemoryManager
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class GenieAgentService:
    """Main service class for the Genie Agent"""
    SYSTEM_PROMPT = (
        "You are Genie, a helpful assistant with access to tools and conversation history. "
             "Use the conversation history to provide contextual responses. "
             "If you can answer directly from your knowledge and the conversation, do so. "
             "When no tool is relevant, answer directly and do not call any tool."
             "Provide only the final answer in your response. "
             "Do not output any intermediate thinking or reasoning."
    )


    def __init__(self, mcp_config: Dict[str, Any]):
        self.mcp_client = MultiServerMCPClient(mcp_config)
        # modern agent instance from create_agent
        self.agent = None
        self.tools = []
        self.config = AgentConfig()
        self.memory_mgr = MemoryManager(self.config); self.memory = self.memory_mgr.memory
        # self.prompt = self._create_default_prompt()
        self.prompt = self.SYSTEM_PROMPT
        self._init_lock = asyncio.Lock()
        self.last_scratchpad: Optional[Dict[str, Any]] = None  # Store last execution details

    def _create_default_prompt(self) -> ChatPromptTemplate:
        """Create the default prompt template with memory"""
        return ChatPromptTemplate.from_messages([
            ("system", 
             "You are Genie, a helpful assistant with access to tools and conversation history. "
             "Use the conversation history to provide contextual responses. "
             "If you can answer directly from your knowledge and the conversation, do so. "
             "When no tool is relevant, answer directly and do not call any tool."
             "Provide only the final answer in your response. "
             "Do not output any intermediate thinking or reasoning."),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
    
    async def initialize(self) -> None:
        """Initialize the agent with MCP tools"""
        async with self._init_lock:
            try:
                logger.info("Loading MCP tools...")
                self.tools = await self.mcp_client.get_tools()
                logger.info(f"Loaded {len(self.tools)} MCP tools")
            except Exception as e:
                logger.error(f"Failed to load MCP tools: {e}")
                self.tools = []
            
            await self._rebuild_agent()
            logger.info("Agent initialized successfully")

    # We replaced AgentExecutor with create_agent because LangChain v1+ uses a new graph-based agent design.
    # create_agent handles tool-calls internally, so we no longer build the executor manually.
    async def _rebuild_agent(self) -> None:
        """Rebuild the agent with current configuration (latest style)."""
        try:
            llm = create_llm_from_registry(
                profile_name=self.config.profile_name,
                model=self.config.model_name,
            )
            logger.info(
                "Created LLM: %s/%s",
                self.config.profile_name,
                self.config.model_name,
            )

            if llm is None:
                logger.error("LLM not configured (LLM value: %s)", llm)
                raise Exception("LLM not configured")

            # Update memory manager with LLM for accurate token counting
            self.memory_mgr.set_llm(llm)

            # create_agent automatically manages chat_history, input, and agent_scratchpad placeholders
            # System prompt is prepended to structure the LLM's behavior and tool usage
            # Build modern agent (LangGraph-based) instead of AgentExecutor
            self.agent = create_agent(
                model=llm,
                tools=self.tools,
                system_prompt= self.prompt,
            )

            logger.info("Agent (create_agent) created successfully")

        except Exception as e:
            logger.error("Failed to build agent: %s", e, exc_info=True)
            raise


    async def update_model(self, profile_name: str, model_name: str) -> None:
        """Update the model configuration and rebuild agent"""
        logger.info(f"Updating model: {profile_name}/{model_name}")
        self.config.profile_name = profile_name
        self.config.model_name = model_name
        await self._rebuild_agent()
    
    def get_conversation_history(self) -> list:
        """Get the current conversation history"""
        return self.memory.chat_memory.messages   

    # We replaced AgentExecutor with create_agent because LangChain v1+ uses a new graph-based agent design.
    # create_agent handles tool-calls internally, so we no longer build the executor manually.
    async def ask_question(self, question: str) -> str:
        """Process a question through the agent (latest create_agent style)."""
        if not self.agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        question = question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        try:
            logger.info("Processing question: %s...", question[:100])

            # 1) Add user message to memory
            self.memory.chat_memory.add_message(HumanMessage(content=question))

            # 2) Build state for the agent: full conversation as `messages`
            state = {
                "messages": self.memory.chat_memory.messages
            }

            # 3) Run the agent
            response_state = await self.agent.ainvoke(
                state,
                config={"recursion_limit": self.config.max_iterations},
            )

            # 4) Extract answer
            result = self._process_response(response_state)

            # 5) Add assistant reply to memory
            self.memory.chat_memory.add_message(AIMessage(content=result))

            # 6) Optional: store debug info + trim memory
            # self._store_scratchpad_info(response_state, question)
            self.memory_mgr.check_memory_status()

            return result

        except Exception as e:
            logger.error("Error processing question: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    # create_agent produces empty AI messages when calling tools, so we must ignore those.
    # The correct final output is always the last non-empty AIMessage in the returned state.
    def _process_response(self, response: Any) -> str:
        # State dict from create_agent
        if isinstance(response, dict) and "messages" in response:
            messages = response["messages"]

            # Walk from the end and pick the last AI message with non-empty content
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and msg.content:
                    return msg.content

            # Fallback: if no AIMessage has content, return last message's content/string
            if messages:
                last = messages[-1]
                return getattr(last, "content", str(last)) or ""

        # Direct AIMessage (just in case)
        if isinstance(response, AIMessage):
            return response.content
        # Generic fallback
        return str(response) if response else ""


    def list_registry_profile_names(self) -> List[str]:		
        profiles = list_registry_profile_names()
        logger.info(f"Listing registry profile names: {profiles}")
        return profiles


    def save_memory(self, file_path: str) -> str:
        """Save conversation memory to a JSON file"""
        try:            
            # Get conversation history
            messages = self.memory.chat_memory.messages
            
            # Format messages for JSON
            conversation_data = {
                "timestamp": datetime.now().isoformat(),
                "total_messages": len(messages),
                "total_tokens": self.memory_mgr._total_tokens(),
                "messages": []
            }
            
            for msg in messages:
                content = msg.content
                # Handle list content
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            content = " ".join([item.get("text", "")])
                        else:
                            content = item.get("text", "")
                
                message_type = "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
                conversation_data["messages"].append({
                    "role": message_type,
                    "content": str(content)
                })
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Conversation saved to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save memory: {str(e)}")

    def load_memory(self, file_path: str) -> str:
        """Load conversation memory from a JSON file"""
        try:            
            # Load conversation history into memory
            with open(file_path, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
            self.memory.chat_memory.clear()
            for msg in conversation_data["messages"]:
                # Create proper message objects based on role
                if msg["role"] == "user":
                    self.memory.chat_memory.add_message(HumanMessage(content=msg["content"]))
                else:  # assistant
                    self.memory.chat_memory.add_message(AIMessage(content=msg["content"]))
            logger.info(f"Conversation loaded from {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to load memory: {str(e)}")
