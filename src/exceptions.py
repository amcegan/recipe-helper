class RecipeHelperError(Exception):
    """Base exception for all Recipe Helper errors."""
    pass

class AppValidationError(RecipeHelperError):
    """Exception raised when data validation fails."""
    pass

class AppAPIError(RecipeHelperError):
    """Exception raised when an external API call fails."""
    pass

class AppVisionError(AppAPIError):
    """Exception raised for errors in the Vision Pipeline."""
    pass

class AppRecipeError(AppAPIError):
    """Exception raised for errors in the Recipe Pipeline."""
    pass
