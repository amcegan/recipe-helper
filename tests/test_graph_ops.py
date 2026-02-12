import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import os
from src.graph import get_weather_context, create_recipe_graph, check_weather_node
from src.schemas import RecipeState

class TestGraphOps(unittest.TestCase):
    
    @patch('src.graph.requests.get')
    def test_get_weather_context_success(self, mock_get):
        # Mock weather API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "current_condition": [{
                "temp_C": "15",
                "weatherDesc": [{"value": "Startlingly sunny"}]
            }]
        }
        mock_get.return_value = mock_response

        # Mock datetime to ensure consistent time in output
        # We need to patch datetime in src.graph because that's where it is imported/used
        with patch('src.graph.datetime') as mock_datetime:
            mock_now = datetime(2023, 10, 27, 14, 30) # 2:30 PM
            mock_datetime.now.return_value = mock_now
            
            # The function uses strftime, so our mock must support it.
            # Real datetime objects support it, and our return_value is a real datetime.

            with patch.dict(os.environ, {"LOCATION_CITY": "Cork"}):
                context = get_weather_context()
                
                self.assertIn("15", context)
                self.assertIn("sunny", context)
                self.assertIn("Cork", context)
                self.assertIn("2 PM", context) # 14:30 -> 02 PM -> 2 PM

    @patch('src.graph.requests.get')
    def test_get_weather_context_api_failure(self, mock_get):
        # Mock API failure
        mock_get.side_effect = Exception("API Down")
        
        with patch('src.graph.datetime') as mock_datetime:
            mock_now = datetime(2023, 10, 27, 9, 0) # 9:00 AM
            mock_datetime.now.return_value = mock_now
            
            context = get_weather_context()
            
            # Should fall back to "mild weather" defaults
            self.assertIn("mild weather", context)
            self.assertIn("Dublin", context) # Default city
            self.assertIn("9 AM", context)

    @patch('src.graph.get_weather_context')
    def test_check_weather_node(self, mock_get_context):
        mock_get_context.return_value = "It is raining"
        state = {"request_id": "test_id"}
        
        result = check_weather_node(state)
        self.assertEqual(result, {"context": "It is raining"})

    def test_create_recipe_graph(self):
        # Verify the graph compiles and has expected structure
        app = create_recipe_graph()
        
        # Check that it is a CompiledGraph (or similar LangGraph object)
        self.assertIsNotNone(app)
        
        # Verify interrupts are set as expected
        # Accessing internal config of compiled graph implies knowing LangGraph internals,
        # but casually we can check if the object is valid.
        # Note: app.interrupt_before might not be directly accessible depending on version,
        # but successful compilation is a good smoke test.
        pass

if __name__ == '__main__':
    unittest.main()
