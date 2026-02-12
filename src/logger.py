import logging
import uuid
from typing import Optional
from src.config import settings
from src.security import safe_error_message

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
        
        # Read log level from centralized settings
        level = getattr(logging, settings.log_level, logging.INFO)
        logger.setLevel(level)
    return logger

def get_request_logger(request_id: Optional[str] = None) -> logging.LoggerAdapter:
    """Returns a logger adapter with a unique request ID."""
    if not request_id:
        request_id = str(uuid.uuid4())[:8]
    logger = setup_logger()
    return logging.LoggerAdapter(logger, {"request_id": request_id})

def log_retry(retry_state):
    """Callback for tenacity to log retry attempts."""
    # Attempt to extract request_id from the function arguments if possible
    # tenacity provides the function in retry_state.fn and arguments in retry_state.args/kwargs
    # Our service methods have request_id as the last or named argument
    request_id = "unknown"
    if 'request_id' in retry_state.kwargs:
        request_id = retry_state.kwargs['request_id']
    elif retry_state.args:
        # For our specific methods: extract_ingredients(self, image, request_id)
        # or suggest_recipes(self, ingredients, preference, request_id)
        # request_id is usually at the end
        request_id = retry_state.args[-1]

    logger = get_request_logger(request_id)
    attempt_num = retry_state.attempt_number
    exception = retry_state.outcome.exception()
    safe_exception_msg = safe_error_message(exception)
    next_step = f"retrying in {retry_state.next_action.sleep}s" if retry_state.next_action else "final attempt failed"
    
    logger.warning(f"Retry attempt {attempt_num} failed: {safe_exception_msg}. {next_step}")
