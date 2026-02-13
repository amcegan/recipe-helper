import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from recipe_helper.recipes import RecipePipeline
from recipe_helper.schemas import RecipeSuggestionList, RecipeSuggestion, FinalRecipe, Ingredient
from recipe_helper.exceptions import AppRecipeError, AppValidationError

@pytest.fixture
def recipe_pipeline():
    return RecipePipeline(api_key="fake_key")

@pytest.mark.asyncio
async def test_suggest_recipes_success(recipe_pipeline):
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
    
    with patch.object(recipe_pipeline.client.aio.models, 'generate_content', new_callable=AsyncMock, return_value=mock_response):
        ingredients = [Ingredient(name="lettuce", confidence=1.0)]
        result = await recipe_pipeline.suggest_recipes(ingredients, "healthy", "fake_context", "test_id")
        
        assert isinstance(result, RecipeSuggestionList)
        assert len(result.suggestions) == 1
        assert result.suggestions[0].title == "Salad"

@pytest.mark.asyncio
async def test_generate_final_recipe_success(recipe_pipeline):
    mock_response = MagicMock()
    mock_response.parsed = FinalRecipe(
        title="Salad", 
        ingredients=["lettuce"], 
        steps=["1. wash", "2. eat"], 
        cooking_time="10 mins"
    )
    
    with patch.object(recipe_pipeline.client.aio.models, 'generate_content', new_callable=AsyncMock, return_value=mock_response):
        ingredients = [Ingredient(name="lettuce", confidence=1.0)]
        result = await recipe_pipeline.generate_final_recipe("Salad", ingredients, "healthy", "fake_context", "test_id")
        
        assert isinstance(result, FinalRecipe)
        assert result.title == "Salad"
        assert len(result.steps) == 2

@pytest.mark.asyncio
async def test_suggest_recipes_empty_response(recipe_pipeline):
    mock_response = MagicMock()
    mock_response.parsed = None
    
    with patch.object(recipe_pipeline.client.aio.models, 'generate_content', new_callable=AsyncMock, return_value=mock_response):
        ingredients = [Ingredient(name="lettuce", confidence=1.0)]
        with pytest.raises(AppRecipeError, match="Empty parsed response"):
            await recipe_pipeline.suggest_recipes(ingredients, "healthy", "fake_context", "test_id")

@pytest.mark.asyncio
async def test_generate_final_recipe_validation_error(recipe_pipeline):
    mock_response = MagicMock()
    # Missing required fields like steps
    mock_response.parsed = MagicMock(spec=["title"]) 
    mock_response.parsed.title = "Salad"
    
    with patch.object(recipe_pipeline.client.aio.models, 'generate_content', new_callable=AsyncMock, return_value=mock_response):
        ingredients = [Ingredient(name="lettuce", confidence=1.0)]
        with pytest.raises(AppValidationError, match="Invalid final recipe format"):
            await recipe_pipeline.generate_final_recipe("Salad", ingredients, "healthy", "fake_context", "test_id")

@pytest.mark.asyncio
async def test_suggest_recipes_retry_success(recipe_pipeline):
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
    
    with patch.object(recipe_pipeline.client.aio.models, 'generate_content', new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = [Exception("Transient Error"), mock_response]
        
        ingredients = [Ingredient(name="lettuce", confidence=1.0)]
        # Reduce retry wait for tests
        with patch('recipe_helper.recipes.wait_exponential', return_value=pytest.importorskip("tenacity").wait_none()):
            result = await recipe_pipeline.suggest_recipes(ingredients, "healthy", "fake_context", "test_id")
            
            assert mock_gen.call_count == 2
            assert result.suggestions[0].title == "Salad"

@pytest.mark.asyncio
async def test_suggest_recipes_all_retries_fail(recipe_pipeline):
    with patch.object(recipe_pipeline.client.aio.models, 'generate_content', new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = Exception("Permanent Error")
        
        ingredients = [Ingredient(name="lettuce", confidence=1.0)]
        # Reduce retry wait for tests
        with patch('recipe_helper.recipes.wait_exponential', return_value=pytest.importorskip("tenacity").wait_none()):
            with pytest.raises(AppRecipeError):
                await recipe_pipeline.suggest_recipes(ingredients, "healthy", "fake_context", "test_id")
            
            assert mock_gen.call_count == 3
