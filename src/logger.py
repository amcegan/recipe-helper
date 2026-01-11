import logging
import uuid
from typing import Optional
import os

def setup_logger(name: str = "recipe_helper") -> logging.Logger:
    """Sets up a logger with a consistent format and unique request IDs."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [RequestID: %(request_id)s] - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Read log level from environment, default to INFO if not set or invalid
        level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_name, logging.INFO)
        logger.setLevel(level)
    return logger

def get_request_logger(request_id: Optional[str] = None) -> logging.LoggerAdapter:
    """Returns a logger adapter with a unique request ID."""
    if not request_id:
        request_id = str(uuid.uuid4())[:8]
    logger = setup_logger()
    return logging.LoggerAdapter(logger, {"request_id": request_id})
