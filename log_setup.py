"""Setup logging logic."""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

def setup_logging(
    log_level: int = logging.INFO,
    max_bytes: int = 10*1024*1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """Configure logging with rotation for both a main log file and an errors-only file.

    Args:
        log_level: Overall logging level
        max_bytes: Maximum size per log file before rotation
        backup_count: Number of backup files to keep

    """
    log_dir: str = Path(os.getenv("LOG_DIR"))
    main_log_file: str = os.getenv("MAIN_LOG_FILE")
    error_log_file: str = os.getenv("ERROR_LOG_FILE")
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Setup main log file handler (captures all logs)
    main_handler = RotatingFileHandler(
        log_dir / main_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    main_handler.setFormatter(formatter)
    main_handler.setLevel(log_level)
    logger.addHandler(main_handler)

    # Setup error log file handler (only captures ERROR and CRITICAL)
    error_handler = RotatingFileHandler(
        log_dir / error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)  # Only log ERROR and above
    logger.addHandler(error_handler)

    # Optionally add console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    return logger
