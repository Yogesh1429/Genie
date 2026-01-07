import uvicorn
import logging
from contextlib import asynccontextmanager
# from dotenv import load_dotenv
from .core.agent_service import GenieAgentService
from .api.routes import create_routes
from ..config_loader import get_mcp
# load_dotenv()

try:
    from ..log_setup import setup_logging
    if not logging.getLogger().handlers:
    	setup_logging()
except ImportError:
    # Running directly 
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@asynccontextmanager
async def lifespan(app):
        # Startup
    try:
        await agent_service.initialize()
        agent_service.init_error = None
        logging.info("🚀 GenIE Agent initialized with MCP tools")
        logging.info("🚀 GenIE Agent started successfully")
    except Exception as e:
        logging.error(f"Agent initialization failed: {str(e)}")
        error_msg = f"ERROR: {str(e)}"
        agent_service.init_error = error_msg
        # print(f"{error_msg}", flush=True)  # This should reach Delphi ?? Test it with Arun. I think it should.
        # import sys
        # sys.stdout.flush()
        logging.error(error_msg)
        # raise
    
    yield
    # Shutdown
    logging.info("🚀 GenIE Agent is shutting down")

# Global service instance
# mcp_config = {
#     "rag": {
#         "transport": "streamable_http",
#         "url": "http://172.16.4.129:8000/mcp",
#     }
# }
mcp_config = {
    "ztpfgi_help": {
        "type": "http",
        "url": "http://172.16.4.129:8000/mcp",
    }
}
mcp_config = get_mcp()
logging.info("mcp_config: %s", mcp_config)
agent_service = GenieAgentService(mcp_config)
app = create_routes(agent_service)
app.router.lifespan_context = lifespan

#For Testing purposes only
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
