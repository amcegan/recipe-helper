from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Optional
from src.schemas import Ingredient, RecipeSuggestionList, FinalRecipe
from src.logger import get_request_logger
from src.prompts import RECIPE_SUGGESTION_PROMPT, FINAL_RECIPE_PROMPT


class RecipePipeline:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.0-flash"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def suggest_recipes(self, ingredients: List[Ingredient], preference: Optional[str], request_id: str) -> RecipeSuggestionList:
        logger = get_request_logger(request_id)
        logger.debug(f"ENTERING: suggest_recipes with request_id={request_id}, preference={preference}")
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
            
            logger.debug(f"EXITING: suggest_recipes with {len(response.parsed.suggestions)} suggestions")
            return response.parsed
        except Exception as e:
            logger.error(f"Error suggesting recipes: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate_final_recipe(self, suggestion_title: str, ingredients: List[Ingredient], preference: Optional[str], request_id: str) -> FinalRecipe:
        logger = get_request_logger(request_id)
        logger.debug(f"ENTERING: generate_final_recipe for {suggestion_title}, request_id={request_id}")
        logger.info(f"Generating final recipe for: {suggestion_title}")

        ingredient_names = ", ".join([ing.name for ing in ingredients])
        prompt = FINAL_RECIPE_PROMPT.format(
            suggestion=suggestion_title,
            ingredients=ingredient_names,
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
            logger.info(f"Final recipe generated: {response.parsed.title}")
            if not response.parsed:
                raise ValueError("Empty parsed response from Gemini")
            
            logger.debug(f"EXITING: generate_final_recipe for {response.parsed.title}")
            return response.parsed
        except Exception as e:
            logger.error(f"Error generating final recipe: {str(e)}")
            raise
