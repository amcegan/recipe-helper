"""
Security module for sanitizing sensitive data.
Provides utilities for masking API keys and other secrets in logs and UI messages.
"""
import re
from src.config import settings

def mask_secrets(text: str) -> str:
    """
    Scans text for known sensitive strings (like API keys) and masks them.
    Currently masks the Gemini API key if present.

    Args:
        text (str): The input string to sanitize.

    Returns:
        str: The sanitized string with secrets masked.
    """
    if not text:
        return text
        
    masked_text = text
    
    # Identify fields that likely contain sensitive data
    sensitive_patterns = ["key", "token", "password", "secret", "group"]
    
    # Mask any string value from settings that matches sensitive patterns
    # We try different ways to get the model data for compatibility
    try:
        settings_data = settings.model_dump()
    except AttributeError:
        try:
            settings_data = settings.dict()
        except AttributeError:
            settings_data = vars(settings)

    for field, value in settings_data.items():
        if any(pattern in field.lower() for pattern in sensitive_patterns):
            if isinstance(value, str) and value:
                masked_text = masked_text.replace(value, "********")
                
    return masked_text

def safe_error_message(e: Exception) -> str:
    """
    Converts an exception to a sanitized string suitable for UI display or logs.

    Args:
        e (Exception): The exception to sanitize.

    Returns:
        str: A masked and sanitized error message.
    """
    raw_msg = str(e)
    return mask_secrets(raw_msg)
