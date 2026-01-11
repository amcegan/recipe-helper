from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential
from PIL import Image
from typing import List, Optional
from src.schemas import IngredientList
from src.logger import get_request_logger
from src.prompts import INGREDIENT_EXTRACTION_PROMPT


class VisionPipeline:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.0-flash"   # Multi-modal model

    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def extract_ingredients(self, image: Image.Image, request_id: str) -> IngredientList:
        logger = get_request_logger(request_id)
        logger.debug(f"ENTERING: extract_ingredients with request_id={request_id}")
        logger.info("Starting ingredient extraction from image")

        try:
            response = self.client.models.generate_content(
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
                raise ValueError("Failed to extract ingredients from image")

            # Explicitly validate against Pydantic model else ValidationError
            IngredientList.model_validate(response.parsed)

            logger.info(f"Successfully extracted {len(response.parsed.ingredients)} ingredients")
            logger.debug(f"EXITING: extract_ingredients")
            return response.parsed
        except Exception as e:
            logger.error(f"Error during extraction: {str(e)}")
            raise
