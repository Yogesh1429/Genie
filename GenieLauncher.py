# main.py
import asyncio
import os
import argparse
import logging
import sys
from uvicorn import Config, Server
from genie.log_setup import setup_logging
from genie.config_loader import get_log_path, get_log_level, get_max_tokens_in_memory, load_config, get_log_retention_days, get_chat_history_path

logger = logging.getLogger(__name__)

async def run_server(app_to_run, host, port):
    config = Config(app_to_run, host=host, port=port, log_config=None,
        # ADD THESE OPTIMIZATIONS (05DEC):
        http="httptools",  # Use faster HTTP parser
        ws="websockets",  # Optimize WebSocket handling
        lifespan="on",  # Enable lifespan events
        access_log=False,  # Disable access logging for better performance
        server_header=False,  # Remove server header
        date_header=False,  # Remove date header
        )
    server = Server(config)
    await server.serve()
    
def get_app(mode=None):
    normalized_mode = (mode or os.getenv("APP_MODE", "genie")).lower()
    logger.info(f"Initializing {normalized_mode} application")
    if normalized_mode == "genie":
        logger.info("🤖 Loading GenIE Agent")
        from genie.agent.main import app  # FastAPI() instance named `app`
        return app
    elif normalized_mode == "qcli":
        logger.info("🤖 Loading GenIE -Amazon Kiro CLI")
        from genie.amazonq.main import app
        return app
    logger.error(f"Invalid APP_MODE={normalized_mode}; expected 'genie' or 'qcli'")
    raise RuntimeError(f"Invalid APP_MODE={normalized_mode}; expected 'genie' or 'qcli'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genie Launcher")
    parser.add_argument("-m", "--app-mode", dest="app_mode", choices=["genie", "qcli"], help="Which app to run")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"), help="Host to bind")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")), help="Port to bind")
    parser.add_argument("--config", type=str, dest="config_file", help="Path to app_config.json")  
    parser.add_argument("--log-path", type=str, dest="log_path", help="Log file location")
    parser.add_argument("--chat-history-path", type=str, dest="chat_history_path", help="Chat history file location")
    parser.add_argument("--providers-file", type=str, dest="providers_file", help="get the providers info")
    args = parser.parse_args()
    
    try:
        if args.config_file:
            os.environ["APP_CONFIG_FILE"] = args.config_file 

        if args.providers_file:
            os.environ["providers_file"] = args.providers_file

        # Setup logging for the entire application
        cfg = load_config()
        log_level = get_log_level()
        log_path = args.log_path
        chat_history_path = args.chat_history_path
        if not log_path:
            log_path = get_log_path()
        log_days = get_log_retention_days()
        max_tokens_in_memory = get_max_tokens_in_memory()
        os.environ["MAX_TOKENS_IN_MEMORY"] = str(max_tokens_in_memory)
        logger.info(f"Chat history path from args: {chat_history_path}")
        if not chat_history_path:
            chat_history_path = get_chat_history_path()
        else:
            os.environ["GENIE_CHAT_HISTORY_PATH"] = chat_history_path
            logger.info(f"Chat history path: {chat_history_path}")

        setup_logging(log_level=log_level, log_dir=log_path, log_retention_days=log_days)

        logger = logging.getLogger('GenieLauncher')
        logger.info(f"Config: {os.environ["APP_CONFIG_FILE"]}")
        logger.info(f"Providers file: {os.environ['providers_file']}")
        logger.debug(f"Log level: {log_level}")
        logger.debug(f"Log path: {log_path}")
        logger.debug(f"Log retention days: {log_days}")
        logger.debug(f"Chat history path: {chat_history_path}")
        logger.info("Starting Genie Launcher")
        logger.info(f"Parsed arguments: mode={args.app_mode}, host={args.host}, port={args.port}")
        logger.info(f"Max tokens in memory: {max_tokens_in_memory}")
        if args.app_mode:
            logger.info(f"Overriding APP_MODE environment variable with: {args.app_mode}")

        app_to_run = get_app(args.app_mode)
        logger.info(f"Starting server on {args.host}:{args.port}")

    # import uvicorn

    # uvicorn.run(app_to_run, host=args.host, port=args.port, log_config=None)
    
        asyncio.run(run_server(app_to_run, args.host, args.port))
        logger.info("Server shut down normally")
        sys.exit(0)
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully 
        if 'logger' in locals():
            logger.info("Server stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        # Handle other exceptions gracefully
        error_msg = f"ERROR: {str(e)}"
        if 'logger' in locals():
            logger.error(error_msg)  # Safe to use
    
        print(error_msg, flush=True)
        sys.stdout.flush()
        sys.exit(1)