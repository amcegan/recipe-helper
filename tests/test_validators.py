import pytest
import json
from pydantic import BaseModel
from src.validators import validate_llm_json, retry_llm_call
from src.exceptions import AppValidationError

# Minimal schema for testing
class UserSchema(BaseModel):
    name: str
    age: int

def test_validate_llm_json_wrapped_success():
    """Verify JSON cleaning and validation in one go."""
    content = "```json\n" + '{"name": "Bob", "age": 25}' + "\n```"
    result = validate_llm_json(content, UserSchema, "test-id")
    assert result.name == "Bob"

def test_validate_llm_json_decode_error():
    content = '{"name": "Alice", "age": 30'  # Missing closing brace
    with pytest.raises(AppValidationError, match="Invalid JSON format"):
        validate_llm_json(content, UserSchema, "test-id")

def test_validate_llm_json_validation_error():
    content = '{"name": "Alice", "age": "not-a-number"}'
    with pytest.raises(AppValidationError, match="Schema validation failed"):
        validate_llm_json(content, UserSchema, "test-id")

def test_retry_llm_call_success_on_retry():
    """Verify recovery after an initial failure."""
    calls = []
    def mock_func():
        calls.append(True)
        if len(calls) == 1:
            raise ValueError("Failure 1")
        return "Success"
    
    result = retry_llm_call(mock_func, max_retries=2)
    assert result == "Success"
    assert len(calls) == 2
