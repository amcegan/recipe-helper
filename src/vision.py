"""
Vision pipeline module for processing images using Gemini.
Handles ingredient extraction from uploaded photos.
"""
import os
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential
from PIL import Image
from typing import List
from src.schemas import IngredientList
from src.logger import get_request_logger, log_retry, log_entry_exit
from src.prompts import INGREDIENT_EXTRACTION_PROMPT
from src.exceptions import AppVisionError, AppValidationError
from src.executor import run_cpu_bound
from src.config import settings

class VisionPipeline:
    """
    Pipeline for handling ingredient extraction from images using Gemini-2.0-flash.
    """
    def __init__(self, api_key: str):
        """
        Initializes the VisionPipeline with a Gemini API key.

        Args:
            api_key (str): The Google Gemini API key.
        """
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.0-flash"   # Multi-modal model
        self.confidence_threshold = settings.ingredient_confidence_threshold

    
    @log_entry_exit
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        after=log_retry,
        reraise=True
    )
    async def extract_ingredients(self, image: Image.Image, request_id: str) -> IngredientList:
        """
        Extracts a list of ingredients from a PIL Image.
        Includes retry logic and confidence threshold filtering.

        Args:
            image (Image.Image): The PIL Image to process.
            request_id (str): Unique request identifier for logging.

        Returns:
            IngredientList: A Pydantic model containing the extracted ingredients.

        Raises:
            AppVisionError: If the Gemini API fails or returns no content.
            AppValidationError: If the returned data does not match the expected schema.
        """
        logger = get_request_logger(request_id)
        logger.info("Starting ingredient extraction from image")

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=[INGREDIENT_EXTRACTION_PROMPT, image],
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=IngredientList,
                    temperature=0.1,
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
                logger.error("No parsed content in Gemini response")
                raise AppVisionError("Failed to extract ingredients from image: Empty response")

            # Explicitly validate against Pydantic model else ValidationError
            try:
                await run_cpu_bound(IngredientList.model_validate, response.parsed)
            except Exception as e:
                logger.error(f"Validation failed: {str(e)}")
                raise AppValidationError(f"Invalid ingredient data format: {str(e)}") from e

            # Filter by confidence
            original_count = len(response.parsed.ingredients)
            response.parsed.ingredients = [
                ing for ing in response.parsed.ingredients 
                if ing.confidence >= self.confidence_threshold
            ]
            filtered_count = len(response.parsed.ingredients)
            
            if filtered_count < original_count:
                logger.info(f"Filtered out {original_count - filtered_count} ingredients below {self.confidence_threshold} confidence")

            logger.info("Successfully extracted ingredients", count=filtered_count)
            return response.parsed
        except Exception as e:
            logger.error(f"Error during extraction: {str(e)}")
            if isinstance(e, (AppVisionError, AppValidationError)):
                raise e
            # Re-wrap unexpected exceptions for consistent library interface
            raise AppVisionError(f"Unexpected error in Vision Pipeline: {str(e)}") from e
