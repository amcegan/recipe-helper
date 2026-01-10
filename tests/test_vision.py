import pytest
from unittest.mock import MagicMock, patch
from src.vision import VisionPipeline
from src.schemas import IngredientList, Ingredient
from PIL import Image

@pytest.fixture
def vision_pipeline():
    return VisionPipeline(api_key="fake_key")

def test_extract_ingredients_success(vision_pipeline):
    mock_response = MagicMock()
    mock_response.parsed = IngredientList(ingredients=[
        Ingredient(name="carrot", confidence=0.9, notes="fresh")
    ])
    
    with patch.object(vision_pipeline.client.models, 'generate_content', return_value=mock_response):
        img = Image.new('RGB', (100, 100))
        result = vision_pipeline.extract_ingredients(img, "test_id")
        
        assert isinstance(result, IngredientList)
        assert len(result.ingredients) == 1
        assert result.ingredients[0].name == "carrot"
        assert result.ingredients[0].confidence == 0.9

def test_extract_ingredients_error(vision_pipeline):
    with patch.object(vision_pipeline.client.models, 'generate_content', side_effect=Exception("API Error")):
        img = Image.new('RGB', (100, 100))
        with pytest.raises(Exception, match="API Error"):
            vision_pipeline.extract_ingredients(img, "test_id")
