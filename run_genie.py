# For Testing purposes only

"""Standalone runner for Genie Agent service"""

import logging
import os
from genie.log_setup import setup_logging

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Genie Agent service")
    os.environ["APP_CONFIG_FILE"] = "C:\\Users\\Yogesh\\app_config.json"
    os.environ["providers_file"] = "C:\\Users\\Yogesh\\providers.json"
    from genie.agent.main import app
    import uvicorn
    
    host = "0.0.0.0"
    port = 8000
    logger.info(f"Starting Genie Agent server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)