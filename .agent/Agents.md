# Agents.md - AI Agent Conventions

This file provides specific instructions and conventions for AI assistants (like Google AntiGravity) working on the **Recipe Helper** project. Follow these guidelines to ensure consistency and reliability.

## Build and Execution
- **Environment**: Use Python 3.9+ and a virtual environment.
- **Install Dependencies**: `pip install -r requirements.txt`
- **Configuration**: Copy `.env.example` to `.env` and provide a `GEMINI_API_KEY`.
- **Run Streamlit app**: `streamlit run main.py`

## Testing
- **Run all tests**: `pytest tests/`
- **Run specific module**: `pytest tests/test_vision.py`
- **Environment check**: Always run tests using the project's virtual environment python (`./venv/bin/python3 -m pytest tests/`).

## Technical Stack
- **AI**: Gemini 2.0 Flash (`gemini-2.0-flash`)
- **UI**: Streamlit
- **Validation**: Pydantic v2
- **Reliability**: Tenacity (retries with exponential backoff)
- **Logging**: Python `logging` with custom `RequestLoggerAdapter` for session tracing

## Core Architecture Decisions
- **Safety First**: All LLM calls must have `safety_settings` configured (blocking dangerous content).
- **Structured Output**: Use Gemini's native structured output (JSON mode) via `response_mime_type='application/json'` and Pydantic models in `response_schema`.
- **Explicit Validation**: Always call `Model.model_validate(response.parsed)` to catch hallucinated schemas before they propagate.
- **Library Design**: Components in `src/` should be designed for reusability. Use custom exceptions from `src/exceptions.py`.
- **Externalized Prompts**: Never hardcode prompts in the pipeline logic. Use `src/prompts.py`.

## Coding Standards
- **Naming Conventions**:
    - Variables/Functions: `snake_case`
    - Classes: `PascalCase`
    - Constants: `UPPER_SNAKE_CASE`
- **Logging**: 
    - Use the `get_request_logger(request_id)` helper.
    - All business logic methods must include `request_id` as a required parameter.
    - Log "ENTERING" and "EXITING" for major logic flows at `DEBUG` level.
- **Exception Handling**:
    - Use `AppVisionError`, `AppRecipeError`, and `AppValidationError` for domain-specific failures.
    - Wrap unexpected errors to maintain a clean library interface.
- **Resource Management**: Always use context managers (`with`) for files and images (e.g., `PIL.Image.open`).

## Testing Philosophy
- Every new feature or utility in `src/` must have a corresponding test in `tests/`.
- Use `pytest` with `unittest.mock` for external dependencies (API calls).
- Keep `tests/test_validators.py` minimal (essential logic only).
- Verify all 3 core pipelines: Vision, Recipes, and Validators.

## Environment Variables
- `GEMINI_API_KEY`: Required for model access.
- `LOG_LEVEL`: Controls verbosity (default `INFO`).
- `INGREDIENT_CONFIDENCE_THRESHOLD`: Minimum threshold for ingredient detection (default `0.5`).

## Reference Documentation
- [Google Gemini API](https://ai.google.dev/docs)
- [Streamlit Framework](https://docs.streamlit.io/)
- [Pydantic v2](https://docs.pydantic.dev/)
