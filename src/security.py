import re
from src.config import settings

def mask_secrets(text: str) -> str:
    """
    Scans text for known sensitive strings (like API keys) and masks them.
    Currently masks the Gemini API key if present.
    """
    if not text:
        return text
        
    masked_text = text
    # Mask Gemini API Key
    if settings.gemini_api_key:
        masked_text = masked_text.replace(settings.gemini_api_key, "********")
        
    return masked_text

def safe_error_message(e: Exception) -> str:
    """
    Converts an exception to a sanitized string suitable for UI display or logs.
    """
    raw_msg = str(e)
    return mask_secrets(raw_msg)
