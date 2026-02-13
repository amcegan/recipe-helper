import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from recipe_helper.graph import get_weather_context, create_recipe_graph, check_weather_node
from recipe_helper.schemas import RecipeState

@pytest.mark.asyncio
async def test_get_weather_context_success():
    # Mock httpx.AsyncClient
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "current_condition": [{
            "temp_C": "15",
            "weatherDesc": [{"value": "Startlingly sunny"}]
        }]
    }
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        # Mock datetime to ensure consistent time in output
        with patch('recipe_helper.graph.datetime') as mock_datetime:
            mock_now = datetime(2023, 10, 27, 14, 30) # 2:30 PM
            mock_datetime.now.return_value = mock_now
            
            # Mock settings for city
            with patch('recipe_helper.graph.settings') as mock_settings:
                mock_settings.location_city = "Cork"
                
                context = await get_weather_context()
                
                assert "15" in context
                assert "sunny" in context
                assert "Cork" in context
                assert "2 PM" in context # 14:30 -> 02 PM -> 2 PM

@pytest.mark.asyncio
async def test_get_weather_context_api_failure():
    # Mock httpx.AsyncClient failure
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.side_effect = Exception("API Down")
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        with patch('recipe_helper.graph.datetime') as mock_datetime:
            mock_now = datetime(2023, 10, 27, 9, 0) # 9:00 AM
            mock_datetime.now.return_value = mock_now
            
            with patch('recipe_helper.graph.settings') as mock_settings:
                mock_settings.location_city = "Dublin"
                
                context = await get_weather_context()
                
                # Should fall back to "mild weather" defaults
                assert "mild weather" in context
                assert "Dublin" in context
                assert "9 AM" in context

@pytest.mark.asyncio
async def test_check_weather_node():
    with patch('recipe_helper.graph.get_weather_context', new_callable=AsyncMock) as mock_get_context:
        mock_get_context.return_value = "It is raining"
        state = {"request_id": "test_id"}
        
        result = await check_weather_node(state)
        assert result == {"context": "It is raining"}

def test_create_recipe_graph():
    # Verify the graph compiles and has expected structure
    app = create_recipe_graph()
    assert app is not None
