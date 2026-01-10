import json
from typing import Type, TypeVar, Any
from pydantic import BaseModel, ValidationError
from src.logger import get_request_logger

T = TypeVar("T", bound=BaseModel)

def validate_llm_json(content: str, schema: Type[T], request_id: str) -> T:
    """
    Validates that LLM string content is valid JSON and matches the Pydantic schema.
    Raises ValueError if validation fails.
    """
    logger = get_request_logger(request_id)
    logger.debug("ENTERING: validate_llm_json")
    try:
        # LLM sometimes wraps JSON in code blocks
        clean_content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_content)
        result = schema.model_validate(data)
        logger.debug("EXITING: validate_llm_json - success")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        logger.debug("EXITING: validate_llm_json - error")
        raise ValueError(f"Invalid JSON format: {str(e)}")
    except ValidationError as e:
        logger.error(f"Schema validation error: {str(e)}")
        logger.debug("EXITING: validate_llm_json - error")
        raise ValueError(f"Schema validation failed: {str(e)}")

def retry_llm_call(func: Any, max_retries: int = 2, *args: Any, **kwargs: Any) -> Any:
    """
    Generic retry wrapper for LLM calls that might fail validation.
    """
    logger = get_request_logger(kwargs.get("request_id", "N/A"))
    logger.debug(f"ENTERING: retry_llm_call with func={func.__name__}")
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            result = func(*args, **kwargs)
            logger.debug(f"EXITING: retry_llm_call - success on attempt {attempt}")
            return result
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed: {str(e)}")
            last_error = e
            continue
    logger.debug("EXITING: retry_llm_call - all attempts failed")
    raise last_error
