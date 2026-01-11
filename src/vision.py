from google import genai
from PIL import Image
from typing import List, Optional
from src.schemas import IngredientList
from src.logger import get_request_logger

INGREDIENT_EXTRACTION_PROMPT = """
You are an ingredient-extraction engine.
Analyze the provided image and extract a list of all visible food ingredients.

Rules:
1. No speculation: label uncertain items as "unknown" rather than guessing names.
2. No brands or inferred items (avoid hallucinating missing spices).
3. Confidence required for each ingredient (0.0 to 1.0).
4. Flag harmful or unfamiliar items; for example, identify unknown mushrooms as "unknown".
5. Culinary context only: exclude any non-food or suggestive content.
"""

class VisionPipeline:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.0-flash"

    def extract_ingredients(self, image: Image.Image, request_id: str) -> IngredientList:
        logger = get_request_logger(request_id)
        logger.debug(f"ENTERING: extract_ingredients with request_id={request_id}")
        logger.info("Starting ingredient extraction from image")

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=[INGREDIENT_EXTRACTION_PROMPT, image],
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': IngredientList,
                }
            )
            
            if not response.parsed:
                logger.error("No parsed content in Gemini response")
                raise ValueError("Failed to extract ingredients from image")

            logger.info(f"Successfully extracted {len(response.parsed.ingredients)} ingredients")
            logger.debug(f"EXITING: extract_ingredients with {len(response.parsed.ingredients)} items")
            return response.parsed
        except Exception as e:
            logger.error(f"Error during extraction: {str(e)}")
            raise
