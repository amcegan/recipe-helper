import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.vision import VisionPipeline
from src.schemas import IngredientList, Ingredient
from src.exceptions import AppVisionError, AppValidationError
from PIL import Image

@pytest.fixture
def vision_pipeline():
    return VisionPipeline(api_key="fake_key")

@pytest.mark.asyncio
async def test_extract_ingredients_success(vision_pipeline):
    mock_response = MagicMock()
    mock_response.parsed = IngredientList(ingredients=[
        Ingredient(name="carrot", confidence=0.9, notes="fresh")
    ])

    # mock the aio.models.generate_content method
    with patch.object(vision_pipeline.client.aio.models, 'generate_content', new_callable=AsyncMock, return_value=mock_response):
        img = Image.new('RGB', (100, 100))
        result = await vision_pipeline.extract_ingredients(img, "test_id")
        
        assert isinstance(result, IngredientList)
        assert len(result.ingredients) == 1
        assert result.ingredients[0].name == "carrot"
        assert result.ingredients[0].confidence == 0.9

@pytest.mark.asyncio
async def test_extract_ingredients_error(vision_pipeline):
    with patch.object(vision_pipeline.client.aio.models, 'generate_content', new_callable=AsyncMock, side_effect=Exception("API Error")):
        img = Image.new('RGB', (100, 100))
        with pytest.raises(AppVisionError):
            await vision_pipeline.extract_ingredients(img, "test_id")

@pytest.mark.asyncio
async def test_extract_ingredients_validation_error(vision_pipeline):
    mock_response = MagicMock()
    with patch.object(vision_pipeline.client.aio.models, 'generate_content', new_callable=AsyncMock, return_value=mock_response):
        mock_response.parsed = MagicMock(spec=[]) # No 'ingredients' attribute
        
        img = Image.new('RGB', (100, 100))
        with pytest.raises(AppValidationError):
             await vision_pipeline.extract_ingredients(img, "test_id")

@pytest.mark.asyncio
async def test_extract_ingredients_retry_success(vision_pipeline):
    mock_response = MagicMock()
    mock_response.parsed = IngredientList(ingredients=[
        Ingredient(name="carrot", confidence=0.9)
    ])
    
    with patch.object(vision_pipeline.client.aio.models, 'generate_content', new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = [Exception("Transient Error"), mock_response]
        
        img = Image.new('RGB', (100, 100))
        # Reduce retry wait for tests
        with patch('src.vision.wait_exponential', return_value=pytest.importorskip("tenacity").wait_none()):
            result = await vision_pipeline.extract_ingredients(img, "test_id")
            
            assert mock_gen.call_count == 2
            assert result.ingredients[0].name == "carrot"

@pytest.mark.asyncio
async def test_extract_ingredients_confidence_filtering(vision_pipeline):
    mock_response = MagicMock()
    mock_response.parsed = IngredientList(ingredients=[
        Ingredient(name="carrot", confidence=0.9),
        Ingredient(name="dust", confidence=0.2)
    ])
    
    with patch.object(vision_pipeline.client.aio.models, 'generate_content', new_callable=AsyncMock, return_value=mock_response):
        # Set threshold to 0.5
        vision_pipeline.confidence_threshold = 0.5
        img = Image.new('RGB', (100, 100))
        result = await vision_pipeline.extract_ingredients(img, "test_id")
        
        assert len(result.ingredients) == 1
        assert result.ingredients[0].name == "carrot"
