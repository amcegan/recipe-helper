# Project Creation Prompt: Recipe Helper (LangGraph Edition)

You are building a modular, production-ready Python application that recommends recipes based on photos of ingredients. This application uses **LangGraph** for orchestration and integrates real-time weather context to personalize suggestions.

## High-Level Requirements

1. **Streamlit User Interface**
    - **Stage 1 (Detect)**: Upload image and trigger ingredient/weather detection.
    - **Stage 2 (Suggest)**: Review ingredients, input optional dietary/style preferences, and trigger recipe suggestions.
    - **Stage 3 (Finalize)**: Select a suggestion and generate the full recipe with cooking instructions.
    - **Resource Safety**: Always use context managers for media and file I/O. Convert images to `bytes` for LangGraph serialization.

2. **Orchestration (LangGraph)**
    - Implement a `StateGraph` with nodes for extraction, weather context, recipe suggestion, and final generation.
    - Use `interrupt_before` to pause for user input (preferences and selection).
    - Use `MemorySaver` for in-memory persistence of the orchestration state.

3. **Vision Pipeline (Gemini API)**
    - Use `gemini-2.0-flash` to extract structured ingredient lists from images.
    - Implement confidence filtering via `INGREDIENT_CONFIDENCE_THRESHOLD`.

4. **Weather Context Service**
    - Fetch current weather from `wttr.in` based on a `LOCATION_CITY` env variable.
    - Use Pydantic models to validate the nested JSON response from the API.
    - Combine weather and local Dublin time into a context string for prompting.

5. **Recipe Generation**
    - Use Gemini to suggest 3-5 recipes based on ingredients, user preferences, and situational context.
    - Generate a high-quality final recipe with title, ingredients, steps, and chef's notes.

6. **Centralized Configuration**
    - Use `pydantic-settings` to manage environment variables (`GEMINI_API_KEY`, `LOCATION_CITY`, etc.) in a type-safe manner.
    - Implement "fail-fast" validation to ensure the application does not start with invalid or missing critical secrets.

## Core Modules & Responsibilities

- **`src/graph.py`**: The heart of the application. Defines the graph nodes, state schema, and compiles the workflow with appropriate interrupts.
- **`src/vision.py`**: Encapsulates all vision-related logic and Gemini Vision API interactions.
- **`src/recipes.py`**: Handles text-based Gemini calls for recipe suggestions and final recipe expansion.
- **`src/schemas.py`**: Central repository for all Pydantic models (Ingredients, Recipes, Weather) and the `RecipeState` TypedDict.
- **`src/prompts.py`**: Centralized module for all LLM prompts, ensuring separation of content and logic.
- **`src/logger.py`**: Structured logging with session-based `request_id` tracking.
- **`src/exceptions.py`**: Domain-specific error types for predictable failure handling.
- **`src/config.py`**: Centralized configuration management using Pydantic-Settings.
- **`src/ui.py`**: The Streamlit interface that drives the graph execution and manages state persistence across user sessions.

## Development Guidelines

- **Validation First**: Every external API response (Gemini, Weather) AND application configuration must be validated immediately.
- **Fail Fast**: The application should fail on startup if required configuration is missing.
- **Resilience**: Use `tenacity` for exponential backoff on all network calls.
- **State Integrity**: Do not store non-serializable objects (like PIL Images) in the LangGraph state; convert to bytes and clear after use.
- **Separation of Concerns**: Keep business logic in `src/` and presentation logic in `ui.py`.
- **Modularity**: Prompts should be templated and accept `ingredients`, `context`, and `preference` as variables.

## Security & Secrets

- Load all configuration from a `.env` file using `python-dotenv`.
- Template variable: `GEMINI_API_KEY`, `LOCATION_CITY`, `LOG_LEVEL`, `INGREDIENT_CONFIDENCE_THRESHOLD`.
- Never commit the `.env` file to version control.