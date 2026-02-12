import json
from typing import Type, TypeVar, Any
from pydantic import BaseModel, ValidationError
from src.logger import get_request_logger
from src.exceptions import AppValidationError

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
        raise AppValidationError(f"Invalid JSON format: {str(e)}") from e
    except ValidationError as e:
        logger.error(f"Schema validation error: {str(e)}")
        raise AppValidationError(f"Schema validation failed: {str(e)}") from e
