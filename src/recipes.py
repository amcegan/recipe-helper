"""
Recipe pipeline module for generating suggestions and final recipes using Gemini.
"""
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Optional
from src.schemas import Ingredient, RecipeSuggestionList, FinalRecipe
from src.logger import get_request_logger, log_retry
from src.prompts import RECIPE_SUGGESTION_PROMPT, FINAL_RECIPE_PROMPT
from src.exceptions import AppRecipeError, AppValidationError
from src.executor import run_cpu_bound


class RecipePipeline:
    """
    Pipeline for generating recipe suggestions and detailed recipes using Gemini-2.0-flash.
    """
    def __init__(self, api_key: str):
        """
        Initializes the RecipePipeline with a Gemini API key.

        Args:
            api_key (str): The Google Gemini API key.
        """
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.0-flash"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        after=log_retry,
        reraise=True
    )
    async def suggest_recipes(self, ingredients: List[Ingredient], preference: Optional[str], context: Optional[str], request_id: str) -> RecipeSuggestionList:
        """
        Generates 3-5 recipe suggestions based on a list of ingredients and user preferences.

        Args:
            ingredients (List[Ingredient]): List of available ingredients.
            preference (Optional[str]): User preferences (e.g., "vegetarian").
            context (Optional[str]): Environmental context (e.g., weather/time).
            request_id (str): Unique request identifier for logging.

        Returns:
            RecipeSuggestionList: A list of recipe suggestions.

        Raises:
            AppRecipeError: If the Gemini API fails or returns no content.
            AppValidationError: If the returned data does not match the expected schema.
        """
        logger = get_request_logger(request_id)
        logger.debug(f"ENTERING: suggest_recipes with request_id={request_id}, preference={preference}")
        logger.info(f"Generating recipe suggestions with preference: {preference}")

        ingredient_names = ", ".join([ing.name for ing in ingredients])
        prompt = RECIPE_SUGGESTION_PROMPT.format(
            ingredients=ingredient_names,
            preference=preference or "None",
            context=context or "No specific context available."
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=RecipeSuggestionList,
                    temperature=0.7,
                    max_output_tokens=2048,
                    safety_settings=[
                        types.SafetySetting(
                            category="HARM_CATEGORY_DANGEROUS_CONTENT",
                            threshold="BLOCK_MEDIUM_AND_ABOVE"
                        )
                    ]
                )
            )
            if not response.parsed:
                raise AppRecipeError("Empty parsed response from Gemini during recipe suggestion")
            
            # Explicitly validate against Pydantic model else ValidationError
            try:
                await run_cpu_bound(RecipeSuggestionList.model_validate, response.parsed)
            except Exception as e:
                logger.error(f"Validation failed: {str(e)}")
                raise AppValidationError(f"Invalid recipe suggestion format: {str(e)}") from e
            
            logger.debug(f"EXITING: suggest_recipes with {len(response.parsed.suggestions)} suggestions")
            return response.parsed
        except Exception as e:
            logger.error(f"Error suggesting recipes: {str(e)}")
            if isinstance(e, (AppRecipeError, AppValidationError)):
                raise e
            raise AppRecipeError(f"Unexpected error in Recipe Pipeline (suggestions): {str(e)}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        after=log_retry,
        reraise=True
    )
    async def generate_final_recipe(self, suggestion_title: str, ingredients: List[Ingredient], preference: Optional[str], context: Optional[str], request_id: str) -> FinalRecipe:
        """
        Generates a detailed, full-length recipe for a selected suggestion.

        Args:
            suggestion_title (str): The title of the chosen recipe suggestion.
            ingredients (List[Ingredient]): List of available ingredients.
            preference (Optional[str]): User preferences.
            context (Optional[str]): Environmental context.
            request_id (str): Unique request identifier for logging.

        Returns:
            FinalRecipe: A detailed recipe object including steps and notes.

        Raises:
            AppRecipeError: If the Gemini API fails or returns no content.
            AppValidationError: If the returned data does not match the expected schema.
        """
        logger = get_request_logger(request_id)
        logger.debug(f"ENTERING: generate_final_recipe for {suggestion_title}, request_id={request_id}")
        logger.info(f"Generating final recipe for: {suggestion_title}")

        ingredient_names = ", ".join([ing.name for ing in ingredients])
        prompt = FINAL_RECIPE_PROMPT.format(
            suggestion=suggestion_title,
            ingredients=ingredient_names,
            preference=preference or "None",
            context=context or "No specific context available."
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=FinalRecipe,
                    temperature=0.3,
                    max_output_tokens=4096,
                    safety_settings=[
                        types.SafetySetting(
                            category="HARM_CATEGORY_DANGEROUS_CONTENT",
                            threshold="BLOCK_MEDIUM_AND_ABOVE"
                        )
                    ]
                )
            )
            logger.info(f"Final recipe generated: {response.parsed.title}")
            if not response.parsed:
                raise AppRecipeError("Empty parsed response from Gemini during final recipe generation")
            
            # Explicitly validate against Pydantic model
            try:
                await run_cpu_bound(FinalRecipe.model_validate, response.parsed)
            except Exception as e:
                logger.error(f"Validation failed: {str(e)}")
                raise AppValidationError(f"Invalid final recipe format: {str(e)}") from e
            
            logger.debug(f"EXITING: generate_final_recipe for {response.parsed.title}")
            return response.parsed
        except Exception as e:
            logger.error(f"Error generating final recipe: {str(e)}")
            if isinstance(e, (AppRecipeError, AppValidationError)):
                raise e
            raise AppRecipeError(f"Unexpected error in Recipe Pipeline (final): {str(e)}") from e
