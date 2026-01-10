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
    try:
        # LLM sometimes wraps JSON in code blocks
        clean_content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_content)
        return schema.model_validate(data)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        raise ValueError(f"Invalid JSON format: {str(e)}")
    except ValidationError as e:
        logger.error(f"Schema validation error: {str(e)}")
        raise ValueError(f"Schema validation failed: {str(e)}")

def retry_llm_call(func: Any, max_retries: int = 2, *args: Any, **kwargs: Any) -> Any:
    """
    Generic retry wrapper for LLM calls that might fail validation.
    """
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            continue
    raise last_error
