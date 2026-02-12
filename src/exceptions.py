class RecipeHelperError(Exception):
    """
    Base exception for all Recipe Helper errors.
    
    This is the top-level exception in the project's custom exception hierarchy.
    """
    pass

class AppValidationError(RecipeHelperError):
    """
    Exception raised when data validation fails.
    
    Typically raised when LLM output does not match the expected Pydantic schema
    or when input parameters are invalid.
    """
    pass

class AppAPIError(RecipeHelperError):
    """
    Exception raised when an external API call fails.
    
    Serves as a base class for specific API failures (e.g., Vision or Recipe APIs).
    Should be used when the error is related to network or service availability.
    """
    pass

class AppVisionError(AppAPIError):
    """
    Exception raised for errors specific to the Vision Pipeline.
    
    Raised when the Gemini vision model fails to process an image, returns
    invalid results, or exceeds quota.
    """
    pass

class AppRecipeError(AppAPIError):
    """
    Exception raised for errors specific to the Recipe Pipeline.
    
    Raised when the recipe generation model fails, returns no suggestions,
    or encounters unexpected issues during recipe synthesis.
    """
    pass
