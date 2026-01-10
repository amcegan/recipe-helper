from google import genai
from typing import List, Optional
from src.schemas import Ingredient, RecipeSuggestionList, FinalRecipe
from src.logger import get_request_logger

RECIPE_SUGGESTION_PROMPT = """
You are a professional chef and nutritionist.
Given the ingredient list and an optional user preference, return a list (3–5 elements) of recipes.

Rules:
1. Distinguish clearly between available and missing ingredients.
2. Explain why each recipe matches the preference.
3. Do not include harmful or unknown ingredients.
4. Avoid recipes requiring naked-flame barbecues unless the user asks explicitly.
5. Keep language professional and child friendly—no sexual or violent metaphors.

Available Ingredients: {ingredients}
User Preference: {preference}
"""

FINAL_RECIPE_PROMPT = """
You are a professional chef. Produce a final, detailed recipe based on the chosen suggestion and user preference.

Ensure safety and clarity.
Chosen Recipe Suggestion: {suggestion}
User Preference: {preference}
"""

class RecipePipeline:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.0-flash"

    def suggest_recipes(self, ingredients: List[Ingredient], preference: Optional[str], request_id: str) -> RecipeSuggestionList:
        logger = get_request_logger(request_id)
        logger.info(f"Generating recipe suggestions with preference: {preference}")

        ingredient_names = ", ".join([ing.name for ing in ingredients])
        prompt = RECIPE_SUGGESTION_PROMPT.format(
            ingredients=ingredient_names,
            preference=preference or "None"
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': RecipeSuggestionList,
                }
            )
            if not response.parsed:
                raise ValueError("Empty parsed response from Gemini")
            return response.parsed
        except Exception as e:
            logger.error(f"Error suggesting recipes: {str(e)}")
            raise

    def generate_final_recipe(self, suggestion_title: str, preference: Optional[str], request_id: str) -> FinalRecipe:
        logger = get_request_logger(request_id)
        logger.info(f"Generating final recipe for: {suggestion_title}")

        prompt = FINAL_RECIPE_PROMPT.format(
            suggestion=suggestion_title,
            preference=preference or "None"
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': FinalRecipe,
                }
            )
            if not response.parsed:
                raise ValueError("Empty parsed response from Gemini")
            return response.parsed
        except Exception as e:
            logger.error(f"Error generating final recipe: {str(e)}")
            raise
