import logging
import sys
import uuid
import functools
import time
from typing import Optional, Any, Callable
import structlog
from recipe_helper.config import settings
from recipe_helper.security import safe_error_message

# Shared request ID context
from structlog.contextvars import bind_contextvars, clear_contextvars, get_contextvars

def setup_logger(name: str = "recipe_helper") -> None:
    """Sets up structlog with consistent formatting and environment-specific outputs."""
    
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Use JSON for production (CloudWatch) or if explicitly asked, otherwise pretty-print
    # We detect "production" by checking if AWS_CLOUDWATCH_GROUP is set
    is_production = settings.aws_cloudwatch_group is not None

    if is_production:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Standard logging integration (to handle non-structlog libraries)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )

    # Optional CloudWatch integration via watchtower
    if is_production:
        import watchtower
        import boto3
        
        session = boto3.Session(region_name=settings.aws_region)
        cw_handler = watchtower.CloudWatchLogHandler(
            log_group=settings.aws_cloudwatch_group,
            boto3_session=session,
            send_interval=1,  # Keep it responsive
        )
        
        root_logger = logging.getLogger()
        root_logger.addHandler(cw_handler)

def get_request_logger(request_id: Optional[str] = None) -> Any:
    """Returns a logger and ensures request_id is bound to the context."""
    if request_id:
        bind_contextvars(request_id=request_id)
    elif not get_contextvars().get("request_id"):
        bind_contextvars(request_id=str(uuid.uuid4())[:8])
    
    return structlog.get_logger()

import inspect

def log_entry_exit(func: Callable) -> Callable:
    """Decorator to log function entry and exit with duration. Supports sync and async."""
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = structlog.get_logger()
        start_time = time.perf_counter()
        logger.info(f"Entering {func.__name__} (async)", function=func.__name__)
        try:
            result = await func(*args, **kwargs)
            duration = time.perf_counter() - start_time
            logger.info(
                f"Exiting {func.__name__} (async)", 
                function=func.__name__, 
                duration_ms=round(duration * 1000, 2)
            )
            return result
        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(
                f"Exception in {func.__name__} (async)", 
                function=func.__name__, 
                error=safe_error_message(e),
                duration_ms=round(duration * 1000, 2)
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = structlog.get_logger()
        start_time = time.perf_counter()
        logger.info(f"Entering {func.__name__}", function=func.__name__)
        try:
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start_time
            logger.info(
                f"Exiting {func.__name__}", 
                function=func.__name__, 
                duration_ms=round(duration * 1000, 2)
            )
            return result
        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(
                f"Exception in {func.__name__}", 
                function=func.__name__, 
                error=safe_error_message(e),
                duration_ms=round(duration * 1000, 2)
            )
            raise

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

def log_retry(retry_state):
    """Callback for tenacity to log retry attempts using structlog."""
    request_id = retry_state.kwargs.get('request_id')
    if not request_id and retry_state.args:
        # Heuristic for our specific codebase
        request_id = retry_state.args[-1] if isinstance(retry_state.args[-1], str) else "unknown"
    
    logger = get_request_logger(request_id)
    attempt_num = retry_state.attempt_number
    exception = retry_state.outcome.exception()
    safe_exception_msg = safe_error_message(exception)
    
    logger.warning(
        "Retry attempt failed",
        attempt=attempt_num,
        error=safe_exception_msg,
        next_step=f"retrying in {retry_state.next_action.sleep}s" if retry_state.next_action else "final attempt failed"
    )
