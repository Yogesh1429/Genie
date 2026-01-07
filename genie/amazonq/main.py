import logging
import uvicorn
from contextlib import asynccontextmanager
import os
import sys
from .core.qcli_client import QCLIClient
from .core.json_processor import JSONProcessor
from .api.routes import create_routes
# load_dotenv()

# Handle both direct execution and module import
try:
    from ..log_setup import setup_logging
    if not logging.getLogger().handlers:
    	setup_logging()
except ImportError:
    # Running directly - setup basic logging
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Global instances
json_processor = JSONProcessor()
qcli_client = QCLIClient(json_processor=json_processor)

@asynccontextmanager
async def lifespan(app):
    # Startup
    try:
        logging.getLogger('genie.amazonq.main').info("Kiro CLI service starting up")
        await qcli_client.initialize()
        qcli_client.init_error = None
        logging.getLogger('genie.amazonq.main').info("Kiro CLI service initialized successfully")
    except Exception as e:
        logging.getLogger('genie.amazonq.main').error(f"Kiro CLI initialization failed: {str(e)}")
        error_msg = f"ERROR: {str(e)}"
        qcli_client.init_error = error_msg
        logging.getLogger('genie.amazonq.main').error(error_msg)
    yield
    # Shutdown
    logging.getLogger('genie.amazonq.main').info("Kiro CLI service shutting down")
    qcli_client.close()

# app = create_routes(qcli_client, json_processor)
app = create_routes(qcli_client)
app.router.lifespan_context = lifespan

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)