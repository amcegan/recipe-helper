import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.fixture(autouse=True)
def mock_run_cpu_bound():
    """
    Globally mock run_cpu_bound to just execute the function directly in tests.
    This avoids needing a ProcessPoolExecutor for unit tests.
    """
    async def mock_run(func, *args, **kwargs):
        return func(*args, **kwargs)
    
    # We patch it in the modules where it is imported
    with patch("recipe_helper.vision.run_cpu_bound", side_effect=mock_run), \
         patch("recipe_helper.recipes.run_cpu_bound", side_effect=mock_run), \
         patch("recipe_helper.graph.run_cpu_bound", side_effect=mock_run), \
         patch("recipe_helper.ui.app.run_cpu_bound", side_effect=mock_run):
        yield
