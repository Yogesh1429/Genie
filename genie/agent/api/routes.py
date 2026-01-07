import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
from ..core.agent_service import GenieAgentService
from functools import wraps
import time 
logger = logging.getLogger(__name__)

def calculate_processing_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        processing_time = time.time() - start_time
        formatted_time = f"{processing_time:.2f} s"
       
        # if isinstance(result, dict):
        #     result["timestamp"] = formatted_time
        # elif hasattr(result, '__dict__'):
        #     result.timestamp = formatted_time
       
        # return result
        # Properly handle Pydantic BaseModel instances
        if isinstance(result, BaseModel):
            # Recreate model with updated timestamp
            result_dict = result.model_dump()  # Pydantic v2
            # result_dict = result.dict()  # Use this for Pydantic v1
            result_dict['timestamp'] = formatted_time
            return type(result)(**result_dict)
        elif isinstance(result, dict):
            result["timestamp"] = formatted_time
            return result
       
        # Fallback for other types
        if hasattr(result, 'timestamp'):
            result.timestamp = formatted_time
        return result
    logger.info(f"Processing time: {wrapper}")   
    return wrapper

class PromptRequest(BaseModel):
    question: str

class PromptResponse(BaseModel):
    status_code: int = 200
    answer: str
    memory_config: Dict[str, int]
    # timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: str = "0.00 s"
	
class ModelSelectRequest(BaseModel):
    profile_name: str
    model_name: str

class ModelSelectResponse(BaseModel):
	status_code: int = 200
	message: str

class LLMProfilesResponse(BaseModel):
	status_code: int = 200
	llm_profiles: List[Dict[str, str]]

class ErrorResponse(BaseModel):
	status_code: int = 400
	message: str

class HealthResponse(BaseModel):
	status_code: int = 200
	genie_status: str
	# timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
	timestamp: str = "0.00 s"
	
class SaveMemoryRequest(BaseModel):
	file_path: str

class SaveMemoryResponse(BaseModel):
	status_code: int = 200
	message: str
	# timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
	timestamp: str = "0.00 s"

class LoadMemoryRequest(BaseModel):
	file_path: str

class LoadMemoryResponse(BaseModel):
    status_code: int = 200
    message: str
    memory_config: Dict[str, int]
	# timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: str = "0.00 s"

class RootResponse(BaseModel):
	status_code: int = 200
	message: str
	# timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
	timestamp: str = "0.00 s"

class MemoryHistoryResponse(BaseModel):
	conversation_history: List[Dict[str, str]]
	total_messages: int
	memory_config: Dict[str, int]
	# timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
	timestamp: str = "0.00 s"

def create_routes(agent_service: GenieAgentService) -> FastAPI:
    '''Create routes for the Genie Agent service'''	
    app = FastAPI(title="Genie Agent API")
    
    @app.get("/genie/")
    @calculate_processing_time
    async def root():
        logger.info("/genie/ called")
        return RootResponse(status_code=200, message="🤖 GenIE Agent running", timestamp=datetime.now().isoformat())
    
    @app.get("/genie/health")
    @calculate_processing_time
    async def health():
        logger.info("/genie/health called")
        if agent_service.init_error:
            return HealthResponse(
                status_code=500,
                genie_status="error",
                error_message=agent_service.init_error
            )
        return HealthResponse(
            status_code=200,
            genie_status = "running" if agent_service.agent is not None else "not running"
        )
    
    @app.get("/genie/memory/clear")
    @calculate_processing_time
    async def clear_memory():
        logger.info("/genie/memory/clear called")
        try:
            agent_service.memory_mgr.clear()
            return {"status_code": 200, "message": "Memory cleared successfully", "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/genie/memory/trim")
    async def trim_memory():
        logger.info("/genie/memory/trim called")
        before_count = len(agent_service.memory_mgr.memory.chat_memory.messages)
        agent_service.memory_mgr.trim_if_needed()
        after_count = len(agent_service.memory_mgr.memory.chat_memory.messages)
        return {
            "message": "Memory trimmed",
            "before_count": before_count,
            "after_count": after_count,
            "timestamp": datetime.now().isoformat()
        }
        
    @app.post("/genie/model")
    @calculate_processing_time
    async def update_model(req: ModelSelectRequest)->ModelSelectResponse:
        logger.info("/genie/model called")
        try:
            await agent_service.update_model(req.profile_name, req.model_name)
            return ModelSelectResponse(status_code=200, message="Model updated successfully")
        except Exception as e:
            # return ErrorResponse(status_code=500, message=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/genie/ask", response_model=PromptResponse)
    @calculate_processing_time
    async def ask_question(req: PromptRequest)->PromptResponse:
        logger.info("/genie/ask called")
        try:
            current_tokens = agent_service.memory_mgr._total_tokens()
            request_tokens = agent_service.memory_mgr._estimate_tokens(req.question)
            total_tokens = current_tokens + request_tokens
           
            if total_tokens >= agent_service.config.max_tokens_in_memory:
                return PromptResponse(
                    status_code=400,
                    answer="Token limit reached. Please clear memory",
                    memory_config={
                        "max_tokens_in_memory": agent_service.config.max_tokens_in_memory,
                        "current_tokens": total_tokens,
                        "current_messages": len(agent_service.memory_mgr.memory.chat_memory.messages)
                })
            
            answer = await agent_service.ask_question(req.question)
            memory_config={
                "max_tokens_in_memory": agent_service.config.max_tokens_in_memory,
                "current_tokens": agent_service.memory_mgr._total_tokens(),
                "current_messages": len(agent_service.memory_mgr.memory.chat_memory.messages)
			}
            return PromptResponse(answer=answer, memory_config=memory_config)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            # return PromptResponse(status_code=400, answer=str(e), memory_config={})

    @app.post("/genie/ask/stream")
    async def ask_question_stream(req: PromptRequest):
        return StreamingResponse(
            agent_service.ask_question_stream(req.question),
            media_type="text/event-stream"
        )

    @app.get("/genie/llm/profiles")	
    @calculate_processing_time
    async def list_registry_profile_names()->LLMProfilesResponse:
        logger.info("/genie/llm/profiles called")
        try:
            answer = agent_service.list_registry_profile_names()
            return LLMProfilesResponse(llm_profiles=answer)
        except Exception as e:
            # return ErrorResponse(status_code=500, message=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/genie/memory/save")	
    @calculate_processing_time
    async def save_memory(req: SaveMemoryRequest)->SaveMemoryResponse:
        logger.info("/genie/memory/save called")
        try:
            if req.file_path == '':
                return SaveMemoryResponse(message="File Name is empty", status_code=400)
            answer = agent_service.save_memory(req.file_path)
            return SaveMemoryResponse(message=answer)
        except Exception as e:
            # return ErrorResponse(status_code=500, message=str(e))
            raise HTTPException(status_code=500, detail=str(e))
			
    @app.post("/genie/memory/load")
    @calculate_processing_time
    async def load_memory(req: LoadMemoryRequest)->LoadMemoryResponse:
        logger.info(f"/genie/memory/load called :{req.file_path}")
        try:
            if req.file_path == '':
                return LoadMemoryResponse(message="File Name is empty", status_code=400)
            answer = agent_service.load_memory(req.file_path)
            memory_config={
                "max_tokens_in_memory": agent_service.config.max_tokens_in_memory,
                "current_tokens": agent_service.memory_mgr._total_tokens(),
                "current_messages": len(agent_service.memory_mgr.memory.chat_memory.messages)
            }
            return LoadMemoryResponse(message=answer, memory_config = memory_config)
        except Exception as e:
            # return ErrorResponse(status_code=500, message=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    return app