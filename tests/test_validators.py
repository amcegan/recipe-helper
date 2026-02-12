import pytest
from pydantic import BaseModel
from src.validators import validate_llm_json

# Minimal schema for testing
class UserSchema(BaseModel):
    name: str
    age: int

def test_validate_llm_json_wrapped_success():
    """Verify JSON cleaning and validation in one go."""
    content = "```json\n" + '{"name": "Bob", "age": 25}' + "\n```"
    result = validate_llm_json(content, UserSchema, "test-id")
    assert result.name == "Bob"
