import pytest
from recipe_helper.security import mask_secrets, safe_error_message
from recipe_helper.config import settings
from unittest.mock import patch

def test_mask_secrets_no_secret():
    text = "Hello world"
    assert mask_secrets(text) == "Hello world"

def test_mask_secrets_with_key():
    with patch.object(settings, 'gemini_api_key', 'super-secret-key'):
        text = "Error: API key super-secret-key is invalid"
        assert mask_secrets(text) == "Error: API key ******** is invalid"

def test_safe_error_message():
    with patch.object(settings, 'gemini_api_key', 'secret-123'):
        try:
            raise ValueError("Failed with secret-123")
        except Exception as e:
            msg = safe_error_message(e)
            assert "********" in msg
            assert "secret-123" not in msg

def test_mask_secrets_empty():
    assert mask_secrets("") == ""
    assert mask_secrets(None) is None
