from datetime import datetime
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from ..core.qcli_client import QCLIClient
from ..core.json_processor import JSONProcessor
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
    return wrapper

class ModelSelectRequest(BaseModel):
    model_name: str

class ModelSelectResponse(BaseModel):
	status_code: int = 200
	message: str
class PromptRequest(BaseModel):
    question: str

class PromptResponse(BaseModel):
	status_code: int = 200
	answer: str
	# timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
	timestamp: str = "0.00 s"

class HealthResponse(BaseModel):
	status_code: int = 200
	qcli_status: str
	# timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
	error_message: str = ""
	timestamp: str = "0.00 s"

class ErrorResponse(BaseModel):
	status_code: int = 500
	message: str

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
    # timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: str = "0.00 s"

class AuthUrlResponse(BaseModel):
    status_code: int = 200
    message: str
    auth_url: str
    # timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: str = "0.00 s"

class StartResponse(BaseModel):
    status_code: int = 200
    message: str
    # timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: str = "0.00 s"

class CloseResponse(BaseModel):
    status_code: int = 200
    message: str
    # timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: str = "0.00 s"

# def create_routes(qcli_client: QCLIClient, json_processor: JSONProcessor) -> FastAPI:
def create_routes(qcli_client: QCLIClient) -> FastAPI:
    '''Create routes for the Kiro CLI service'''	
    app = FastAPI(title="Kiro CLI Agent API")
    
    @app.get("/qcli")
    @calculate_processing_time
    async def root()->AuthUrlResponse:
        logger.info("/qcli endpoint called")
        auth_url = qcli_client.auth_url
        if auth_url == "Already logged in":
            return AuthUrlResponse(
                status_code=201, 
                message="GenIE - Kiro CLI is Already Logged in", 
                auth_url="None", # because already logged in
                # timestamp=datetime.now().isoformat()
                timestamp="0.00 s"
            )
        else:
            return AuthUrlResponse(
                status_code=200, 
                message="GenIE - Kiro CLI Logging in", 
                auth_url=auth_url, 
                # timestamp=datetime.now().isoformat()
                timestamp="0.00 s"
            )

    @app.get("/qcli/start")
    @calculate_processing_time
    async def start()->StartResponse:
        logger.info("/qcli/start endpoint called")
        try:
            await qcli_client.launch_q_chat()
            return StartResponse(
                status_code=200, 
                message="Kiro CLI started successfully",
                # timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            logger.error(f"❌ Failed to start Kiro CLI: {e}")
            # return StartResponse(status_code=500, message=str(e), timestamp=datetime.now().isoformat())
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/qcli/close")
    @calculate_processing_time
    async def close()->CloseResponse:
        logger.info("/qcli/close endpoint called")
        try:
            qcli_client.close()
            return CloseResponse(status_code=200, 
                message = "Kiro CLI closed successfully", 
                # timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            logger.error(f"Error: {e}")
            # return CloseResponse(status_code=500, message=str(e), timestamp=datetime.now().isoformat())
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/qcli/health")
    @calculate_processing_time
    async def health()->HealthResponse:
        logger.info("/qcli/health endpoint called")
        logger.info(f"qcli_client.init_error: {qcli_client.init_error}")
        if qcli_client.init_error:
            return HealthResponse(
                status_code=500,
                qcli_status="error",
                error_message=qcli_client.init_error
            )
        return HealthResponse(
            status_code=200,
            qcli_status="running" if qcli_client.child is not None else "not running",
            # timestamp=datetime.now().isoformat()
        )
	
    @app.post("/qcli/model")
    @calculate_processing_time
    async def update_model(req: ModelSelectRequest)->ModelSelectResponse:
        logger.info("/qcli/model endpoint called")
        try:
            logger.info(f"model_name: {req.model_name}")
            response = await qcli_client.update_model(req.model_name)
            return ModelSelectResponse(status_code=200, message=response)
        except Exception as e:
            logger.error(f"Error: {e}")
            # return ModelSelectResponse(status_code=500, message=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/qcli/ask")
    @calculate_processing_time
    async def ask(req: PromptRequest)->PromptResponse:
        logger.info("/qcli/ask endpoint called")
        try:
            # req.question = req.question.replace("\\r", "")
            # req.question = req.question.replace("\r", "")
            #Arun
            # req.question = req.question.replace("\\r", "")
            req.question = req.question.replace("\r\n", "\n").replace("\n", "\\n")
            #Arun
            req.question = req.question.strip()
            if req.question.strip().lower() in ['exit', 'quit']:
                qcli_client.close()
                return PromptResponse(answer='Kiro CLI Closed', status_code=200)

            if req.question.strip() == '':
                return PromptResponse(answer='Invalid prompt', status_code=400)
            
            if req.question.startswith('/'):
                return PromptResponse(answer='Invalid prompt', status_code=400)	
            
            if qcli_client.child is None:
                await qcli_client.initialize()
        
            logger.info(f"Prompt: {req.question}")
            if req.question.startswith('/'):
                response = await qcli_client.ask_question(req.question, timeout=3)
            else:
                response = await qcli_client.ask_question(req.question)
            logger.info(f"req.question with repr : {repr(req.question)}")
            clean = qcli_client.process_response_json(req.question, response)
            # clean = json_processor.process_and_extract_json(req.question, response)
            logger.info(f"Result: {clean}")
            return PromptResponse(answer=clean, status_code=200)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            #  return PromptResponse(answer=str(e), status_code=500)
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/qcli/memory/save")
    @calculate_processing_time
    async def save_memory(req: SaveMemoryRequest)->SaveMemoryResponse:
        logger.info("/qcli/memory/save endpoint called")
        try:
            if req.file_path == '':
                return SaveMemoryResponse(message="File Name is empty", status_code=400)
            response = await qcli_client.save_memory(req.file_path)
            return SaveMemoryResponse(message=response, status_code=200)
        except Exception as e:
            logger.error(f"Error: {e}")
            # return SaveMemoryResponse(message=str(e), status_code=500)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/qcli/memory/load")
    @calculate_processing_time
    async def load_memory(req: LoadMemoryRequest)->LoadMemoryResponse:
        logger.info("/qcli/memory/load endpoint called")
        try:
            if req.file_path == '':
                return LoadMemoryResponse(message="File Name is empty", status_code=400)
            response = qcli_client.load_memory(req.file_path)
            return LoadMemoryResponse(message=response, status_code=200)
        except Exception as e:
            logger.error(f"Error: {e}")
            # return LoadMemoryResponse(message=str(e), status_code=500)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/qcli/memory/clear")
    @calculate_processing_time
    async def clear_memory():
        logger.info("/qcli/memory/clear endpoint called")
        try:
            response = await qcli_client.clear_memory()
            return {"status_code": 200, "message": response, "timestamp": datetime.now().isoformat()
                }
        except Exception as e:  
            logger.error(f"Error: {e}")
            # return {"status_code": 500, "message": str(e), "timestamp": datetime.now().isoformat()}
            raise HTTPException(status_code=500, detail=str(e))
    
    return app