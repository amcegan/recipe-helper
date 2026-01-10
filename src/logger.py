import logging
import uuid
from typing import Optional

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
        logger.setLevel(logging.DEBUG)
    return logger

class RequestLoggerAdapter(logging.LoggerAdapter):
    """Adapter to inject request_id into log records."""
    def process(self, msg, kwargs):
        # Ensure 'extra' exists in kwargs and contains 'request_id'
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs

def get_request_logger(request_id: Optional[str] = None) -> RequestLoggerAdapter:
    """Returns a logger adapter with a unique request ID."""
    if not request_id:
        request_id = str(uuid.uuid4())[:8]
    logger = setup_logger()
    return RequestLoggerAdapter(logger, {"request_id": request_id})
