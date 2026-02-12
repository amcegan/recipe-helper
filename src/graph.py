"""
Orchestration module defining the LangGraph workflow for recipe generation.
Includes weather context fetching, ingredient extraction, and recipe suggestion nodes.
"""
from src.config import settings
import httpx
from datetime import datetime
from typing import List, Optional
from langgraph.graph import StateGraph, START, END
from src.vision import VisionPipeline
from src.recipes import RecipePipeline
from src.schemas import RecipeState, IngredientList, RecipeSuggestionList, FinalRecipe, WeatherResponse
from src.logger import get_request_logger, log_entry_exit
from src.exceptions import AppVisionError, AppRecipeError, AppValidationError
from src.executor import run_cpu_bound
from src.security import safe_error_message

# Constants
WEATHER_API_BASE_URL = "https://wttr.in"

@log_entry_exit
async def get_weather_context():
    """
    Fetches weather context from wttr.in and current Dublin time.

    Returns:
        str: A formatted string describing the current weather and time.
    """
    city = settings.location_city
    
    # Weather API (wttr.in)
    weather_desc = "mild weather"
    try:
        url = f"{WEATHER_API_BASE_URL}/{city}?format=j1"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                # Validate with Pydantic
                weather_data = await run_cpu_bound(WeatherResponse.model_validate, response.json())
                if weather_data.current_condition:
                    current = weather_data.current_condition[0]
                    temp = current.temp_C
                    desc = "mild"
                    if current.weatherDesc:
                        desc = current.weatherDesc[0].value.lower()
                    weather_desc = f"{temp} °C and {desc}"
    except Exception as e:
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

def process_image(b):
    """Helper for multiprocessing image decoding."""
    import io
    with Image.open(io.BytesIO(b)) as img:
        img.load() # Force loading of pixels
        return img

async def extract_ingredients_node(state: RecipeState):
    """
    Node for extracting ingredients from an image.
    Uses VisionPipeline to process the image and extract a list of ingredients.

    Args:
        state (RecipeState): The current graph state.

    Returns:
        dict: A dictionary containing the extracted ingredients or an error message.
    """
    logger = get_request_logger(state['request_id'])
    logger.debug("Processing extraction node", image_type=str(type(state.get('image'))))
    
    if not state.get('image'):
        return {"error": "No image provided for ingredient extraction"}
    
    if not isinstance(state['image'], bytes):
        logger.error(f"Image in state is not bytes! It is {type(state['image'])}")
        return {"error": f"Internal Error: Expected image bytes, got {type(state['image'])}"}

    api_key = settings.gemini_api_key
    vision_pipeline = VisionPipeline(api_key)
    
    try:
        # Decode bytes to PIL Image
        image_bytes = state['image']
        pil_image = await run_cpu_bound(process_image, image_bytes)
        ingredients = await vision_pipeline.extract_ingredients(pil_image, state['request_id'])
        
        # We null out the image to keep the checkpoint size small/serializable
        return {"ingredients": ingredients.ingredients, "image": None}
    except Exception as e:
        logger.error(f"Error in extraction node: {safe_error_message(e)}")
        return {"error": safe_error_message(e)}

async def check_weather_node(state: RecipeState):
    """
    Node for fetching current weather context.
    Calls get_weather_context and updates the state with the context string.

    Args:
        state (RecipeState): The current graph state.

    Returns:
        dict: A dictionary containing the weather context string.
    """
    logger = get_request_logger(state['request_id'])
    logger.debug("Processing weather node")
    context = await get_weather_context()
    return {"context": context}

async def suggest_recipes_node(state: RecipeState):
    """
    Node for generating recipe suggestions.
    Uses RecipePipeline to suggest recipes based on ingredients, preferences, and context.

    Args:
        state (RecipeState): The current graph state.

    Returns:
        dict: A dictionary containing the list of recipe suggestions or an error message.
    """
    logger = get_request_logger(state['request_id'])
    logger.debug("Processing suggestions node")
    
    api_key = settings.gemini_api_key
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
        logger.error(f"Error in suggestions node: {safe_error_message(e)}")
        return {"error": safe_error_message(e)}

async def human_review_node(state: RecipeState):
    """
    Node that serves as an interruption point for human review.
    This node simply returns the current state and is meant to be interrupted.

    Args:
        state (RecipeState): The current graph state.

    Returns:
        RecipeState: The unchanged state.
    """
    # This node will be interrupted.
    return state

async def generate_final_recipe_node(state: RecipeState):
    """
    Node for generating a detailed final recipe.
    Uses RecipePipeline to create a full recipe for the selected suggestion.

    Args:
        state (RecipeState): The current graph state.

    Returns:
        dict: A dictionary containing the final recipe object or an error message.
    """
    logger = get_request_logger(state['request_id'])
    logger.debug("Processing final recipe node")
    
    api_key = settings.gemini_api_key
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
        logger.error(f"Error in final recipe node: {safe_error_message(e)}")
        return {"error": safe_error_message(e)}

# Build Graph

def create_recipe_graph():
    """
    Constructs and compiles the recipe generation graph.
    Defines the nodes, edges, and interruption points for the workflow.

    Returns:
        CompiledGraph: The compiled LangGraph workflow.
    """
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

def get_initial_state(request_id: str) -> RecipeState:
    """
    Creates a new initial state for the recipe generation graph.

    Args:
        request_id (str): Unique request identifier.

    Returns:
        RecipeState: The initial graph state.
    """
    return {
        "image": None,
        "ingredients": None,
        "context": None,
        "suggestions": None,
        "selected_recipe": None,
        "user_preference": "",
        "final_recipe": None,
        "request_id": request_id,
        "error": None
    }

def update_user_preference(graph, config: dict, preference: str):
    """
    Updates the user preference in the graph state.

    Args:
        graph (CompiledGraph): The compiled LangGraph workflow.
        config (dict): Configuration for the graph run (identifies the thread).
        preference (str): The new user preference string.
    """
    graph.update_state(config, {"user_preference": preference})

def update_selected_recipe(graph, config: dict, recipe_title: str):
    """
    Updates the selected recipe title in the graph state.

    Args:
        graph (CompiledGraph): The compiled LangGraph workflow.
        config (dict): Configuration for the graph run.
        recipe_title (str): The title of the selected recipe.
    """
    graph.update_state(config, {"selected_recipe": recipe_title})
