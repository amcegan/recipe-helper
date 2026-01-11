# agents.md - AI Agent Conventions

This file provides specific instructions and conventions for AI assistants working on the **Recipe Helper** project. Follow these guidelines to ensure consistency and reliability.

## Build and Execution
- **Environment**: Use Python 3.9+ and a virtual environment.
- **Install Dependencies**: `pip install -r requirements.txt`
- **Configuration**: Copy `.env.example` to `.env` and providing `GEMINI_API_KEY` and `LOCATION_CITY`.
- **Run Streamlit app**: `streamlit run main.py`

## Testing
- **Run all tests**: `pytest tests/`
- **Graph Compilation**: Verify graph compilation via CLI (`from src.graph import create_recipe_graph`).

## Technical Stack
- **AI**: Gemini 2.0 Flash (`gemini-2.0-flash`)
- **Orchestration**: LangGraph (StateGraph with state persistence)
- **UI**: Streamlit
- **Validation**: Pydantic v2
- **External Tools**: `wttr.in` for weather context, `pytz` for timezone handling

## Core Architecture Decisions
- **Graph-Based Workflow**: The application logic is orchestrated by a LangGraph `StateGraph` in `src/graph.py`. Use `interrupt_before` to implement human-in-the-loop steps.
- **State Serialization**: The graph state (`RecipeState`) must be serializable.
    - **Binary Images**: Convert images to `bytes` before storing in the state.
    - **Cleaning state**: Set large binary objects (like images) to `None` immediately after they are processed by a node to optimize checkpoint size.
- **Situational Context**: Enrich prompts with a `context` string containing local weather and time.
- **Explicit Validation**: Use Pydantic models (e.g., `WeatherResponse`, `IngredientList`) for all external API and LLM responses.

## Coding Standards
- **Graph Nodes**:
    - Log "ENTERING Node: [NodeName]" at `DEBUG` level.
    - Return a dictionary of updates to the state, not the entire state.
- **Logging**: Use the `get_request_logger(request_id)` helper for session tracing.
- **Resource Management**: Always use context managers (`with`) for files, images, and network requests.

## Environment Variables
- `GEMINI_API_KEY`: Required for Gemini model access.
- `LOCATION_CITY`: City for weather context (default `Dublin`).
- `LOG_LEVEL`: Controls verbosity (default `INFO`).
- `INGREDIENT_CONFIDENCE_THRESHOLD`: Minimum threshold for ingredient detection (default `0.5`).

## Reference Documentation
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Google Gemini API](https://ai.google.dev/docs)
- [Pydantic v2](https://docs.pydantic.dev/)
- [wttr.in](https://wttr.in/:help)
