import pytest
from unittest.mock import MagicMock, patch
from src.recipes import RecipePipeline
from src.schemas import RecipeSuggestionList, RecipeSuggestion, FinalRecipe, Ingredient

@pytest.fixture
def recipe_pipeline():
    return RecipePipeline(api_key="fake_key")

def test_suggest_recipes_success(recipe_pipeline):
    mock_response = MagicMock()
    mock_response.parsed = RecipeSuggestionList(suggestions=[
        RecipeSuggestion(
            title="Salad", 
            diet_tags=["vegan"], 
            time_minutes=10, 
            required_ingredients=["lettuce"], 
            missing_ingredients=[], 
            steps=["wash", "eat"], 
            rationale="easy"
        )
    ])
    
    with patch.object(recipe_pipeline.client.models, 'generate_content', return_value=mock_response):
        ingredients = [Ingredient(name="lettuce", confidence=1.0)]
        result = recipe_pipeline.suggest_recipes(ingredients, "healthy", "test_id")
        
        assert isinstance(result, RecipeSuggestionList)
        assert len(result.suggestions) == 1
        assert result.suggestions[0].title == "Salad"

def test_generate_final_recipe_success(recipe_pipeline):
    mock_response = MagicMock()
    mock_response.parsed = FinalRecipe(
        title="Salad", 
        ingredients=["lettuce"], 
        steps=["1. wash", "2. eat"], 
        cooking_time="10 mins"
    )
    
    with patch.object(recipe_pipeline.client.models, 'generate_content', return_value=mock_response):
        ingredients = [Ingredient(name="lettuce", confidence=1.0)]
        result = recipe_pipeline.generate_final_recipe("Salad", ingredients, "healthy", "test_id")
        
        assert isinstance(result, FinalRecipe)
        assert result.title == "Salad"
        assert len(result.steps) == 2
