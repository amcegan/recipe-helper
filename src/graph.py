import os
import httpx
from datetime import datetime
from typing import List, Optional
from langgraph.graph import StateGraph, START, END
from src.vision import VisionPipeline
from src.recipes import RecipePipeline
from src.schemas import RecipeState, IngredientList, RecipeSuggestionList, FinalRecipe, WeatherResponse
from src.logger import get_request_logger
from src.exceptions import AppVisionError, AppRecipeError, AppValidationError

# Constants
WEATHER_API_BASE_URL = "https://wttr.in"

async def get_weather_context():
    """Fetches weather context from wttr.in and current Dublin time."""
    city = os.getenv("LOCATION_CITY", "Dublin")
    
    # Weather API (wttr.in)
    weather_desc = "mild weather"
    try:
        url = f"{WEATHER_API_BASE_URL}/{city}?format=j1"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                # Validate with Pydantic
                weather_data = WeatherResponse.model_validate(response.json())
                current = weather_data.current_condition[0]
                temp = current.temp_C
                desc = current.weatherDesc[0].value.lower()
                weather_desc = f"{temp} °C and {desc}"
    except Exception:
        # Fallback to defaults
        pass

    # System Time
    now = datetime.now()
    time_str = now.strftime("%I %p").lstrip('0')
    
    return f"It is currently {weather_desc} in {city} at {time_str}."

from langgraph.checkpoint.memory import MemorySaver

# Nodes

import io
from PIL import Image

async def extract_ingredients_node(state: RecipeState):
    logger = get_request_logger(state['request_id'])
    logger.debug(f"ENTERING Node: extract_ingredients - Image type: {type(state.get('image'))}")
    
    if not state.get('image'):
        return {"error": "No image provided for ingredient extraction"}
    
    if not isinstance(state['image'], bytes):
        logger.error(f"Image in state is not bytes! It is {type(state['image'])}")
        return {"error": f"Internal Error: Expected image bytes, got {type(state['image'])}"}

    api_key = os.getenv("GEMINI_API_KEY")
    vision_pipeline = VisionPipeline(api_key)
    
    try:
        # Decode bytes to PIL Image
        image_bytes = state['image']
        with Image.open(io.BytesIO(image_bytes)) as pil_image:
            ingredients = await vision_pipeline.extract_ingredients(pil_image, state['request_id'])
        
        # We null out the image to keep the checkpoint size small/serializable
        return {"ingredients": ingredients.ingredients, "image": None}
    except Exception as e:
        logger.error(f"Error in extraction node: {e}")
        return {"error": str(e)}

async def check_weather_node(state: RecipeState):
    logger = get_request_logger(state['request_id'])
    logger.debug("ENTERING Node: check_weather")
    context = await get_weather_context()
    return {"context": context}

async def suggest_recipes_node(state: RecipeState):
    logger = get_request_logger(state['request_id'])
    logger.debug("ENTERING Node: suggest_recipes")
    
    api_key = os.getenv("GEMINI_API_KEY")
    recipe_pipeline = RecipePipeline(api_key)
    
    try:
        suggestions = await recipe_pipeline.suggest_recipes(
            state['ingredients'],
            state['user_preference'],
            state['context'],
            state['request_id']
        )
        return {"suggestions": suggestions.suggestions}
    except Exception as e:
        logger.error(f"Error in suggestions node: {e}")
        return {"error": str(e)}

async def human_review_node(state: RecipeState):
    # This node will be interrupted.
    return state

async def generate_final_recipe_node(state: RecipeState):
    logger = get_request_logger(state['request_id'])
    logger.debug("ENTERING Node: generate_final_recipe")
    
    api_key = os.getenv("GEMINI_API_KEY")
    recipe_pipeline = RecipePipeline(api_key)
    
    try:
        final_recipe = await recipe_pipeline.generate_final_recipe(
            state['selected_recipe'],
            state['ingredients'],
            state['user_preference'],
            state['context'],
            state['request_id']
        )
        return {"final_recipe": final_recipe}
    except Exception as e:
        logger.error(f"Error in final recipe node: {e}")
        return {"error": str(e)}

# Build Graph

def create_recipe_graph():
    workflow = StateGraph(RecipeState)
    
    workflow.add_node("extract_ingredients", extract_ingredients_node)
    workflow.add_node("check_weather", check_weather_node)
    workflow.add_node("suggest_recipes", suggest_recipes_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("generate_final_recipe", generate_final_recipe_node)
    
    workflow.add_edge(START, "extract_ingredients")
    workflow.add_edge("extract_ingredients", "check_weather")
    workflow.add_edge("check_weather", "suggest_recipes")
    workflow.add_edge("suggest_recipes", "human_review")
    workflow.add_edge("human_review", "generate_final_recipe")
    workflow.add_edge("generate_final_recipe", END)
    
    # We interrupt AT suggest_recipes to allow preference input,
    # and AT human_review to let the user select a recipe.
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer, interrupt_before=["suggest_recipes", "human_review"])
