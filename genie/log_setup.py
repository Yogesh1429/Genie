import logging
from datetime import datetime, timedelta
from pathlib import Path
# (05DEC) commented out the old log cleanup code
import threading

def _cleanup_old_logs_async(log_dir: Path, days: int = 30) -> None:
    """Delete .log files asynchronously."""
    def cleanup():
        cutoff_time = datetime.now() - timedelta(days=days)
        logger = logging.getLogger(__name__)
        try:
            for file_path in log_dir.glob('*.log'):
                try:
                    if file_path.is_file():
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if mtime < cutoff_time:
                            file_path.unlink()
                            logger.info(f"Deleted old log file: {file_path}")
                except Exception as exc:
                    logger.warning(f"Failed to delete log file {file_path}: {exc}")
        except Exception as e:
            logger.error(f"Cleanup thread error: {e}")
    
    # Run in daemon thread so it doesn't block startup
    thread = threading.Thread(target=cleanup, daemon=True)
    thread.start()

# def _cleanup_old_logs(log_dir: Path, days: int = 30) -> None:
#     """Delete .log files in log_dir older than the given number of days."""
#     cutoff_time = datetime.now() - timedelta(days=days)
#     logger = logging.getLogger(__name__)
#     for file_path in log_dir.glob('*.log'):
#         try:
#             if file_path.is_file():
#                 mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
#                 if mtime < cutoff_time:
#                     file_path.unlink()
#                     logger.info(f"Deleted old log file: {file_path}")
#         except Exception as exc:
#             logger.warning(f"Failed to delete log file {file_path}: {exc}")

def setup_logging(log_level=logging.DEBUG, log_dir="logs", log_retention_days=30):
    """Setup centralized logging for the entire GenIE-AI package"""
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    # Cleanup old logs (older than 30 days)
    # _cleanup_old_logs(log_path, days=log_retention_days)
    # (05DEC) commented out the old log cleanup code
    _cleanup_old_logs_async(log_path, days=log_retention_days)
    # (05DEC) added the new log cleanup code
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_path / f"genie_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(levelname)s %(name)s(%(funcName)s:%(lineno)d) %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Also log to console
        ],
        force=True
    )
    
    # Route Uvicorn logs through root handlers (file + console)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(name)
        try:
			# Remove any pre-existing handlers so logs propagate to root
            uv_logger.handlers.clear()
        except Exception:
            uv_logger.handlers = []
        uv_logger.propagate = True
        uv_logger.setLevel(logging.WARNING)
    
    # Silence noisy third-party libraries
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Log file: {log_file}")
    
    return str(log_file)