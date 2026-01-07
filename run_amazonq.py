# For Testing purposes only
"""Standalone runner for Amazon Q CLI service"""

import os
import logging
from genie.log_setup import setup_logging

if __name__ == "__main__":
    # Set the config file path
    os.environ["APP_CONFIG_FILE"] = "c:\\GenIE-AI\\config\\app_config.json"
    os.environ["QCLI_USER_NAME"] = "user4"
    os.environ["GENIE_CHAT_HISTORY_PATH"] = "c:\\GenIE-AI\\logs"
    os.environ["providers_file"] = "c:\\GenIE-AI\\config\\providers.json"
  
 
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Amazon Q CLI service")
    
    from genie.amazonq.main import app
    import uvicorn
    
    host = "0.0.0.0"
    port = 8000
    logger.info(f"Starting Amazon Q CLI server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)