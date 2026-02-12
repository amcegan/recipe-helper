from typing import List, Optional
from pydantic import BaseModel, Field

class Ingredient(BaseModel):
    """Model for a single ingredient extracted from an image."""
    name: str = Field(..., description="Name of the ingredient")
    confidence: float = Field(..., description="Confidence score from 0 to 1")
    notes: Optional[str] = Field(None, description="Additional notes or context")

class IngredientList(BaseModel):
    """Model for a list of ingredients extracted from an image."""
    ingredients: List[Ingredient]

class RecipeSuggestion(BaseModel):
    """Model for a recipe suggestion presented to the user."""
    title: str
    diet_tags: List[str]
    time_minutes: int
    required_ingredients: List[str]
    missing_ingredients: List[str]
    steps: List[str]
    rationale: str

class RecipeSuggestionList(BaseModel):
    """Model for a list of recipe suggestions."""
    suggestions: List[RecipeSuggestion]

class FinalRecipe(BaseModel):
    """Model for the detailed final recipe."""
    title: str
    ingredients: List[str]
    steps: List[str]
    cooking_time: str
    notes: Optional[str] = None

class WeatherDesc(BaseModel):
    value: str

class CurrentCondition(BaseModel):
    temp_C: str
    weatherDesc: List[WeatherDesc] = Field(..., min_length=1)

class WeatherResponse(BaseModel):
    current_condition: List[CurrentCondition] = Field(..., min_length=1)

from typing import TypedDict, Annotated
import operator

class RecipeState(TypedDict):
    """State for the LangGraph recipe generation flow."""
    image: Optional[bytes]
    ingredients: Optional[List[Ingredient]]
    context: Optional[str] # Weather/Time
    suggestions: Optional[List[RecipeSuggestion]]
    selected_recipe: Optional[str] # Title
    user_preference: Optional[str]
    final_recipe: Optional[FinalRecipe]
    request_id: str
    error: Optional[str]
