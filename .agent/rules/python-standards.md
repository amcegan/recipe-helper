# Python Development Standards

Enforce professional software engineering practices for the Recipe Helper project.

## Code Style
- Follow PEP 8 guidelines.
- Use explicit type hints for all function arguments and return types.
- Maintain consistent naming: snake_case for variables/functions, PascalCase for classes.
- Include docstrings for all modules, classes, and public functions.

## Modular Architecture
- Business logic must reside in dedicated modules in src/.
- main.py should only handle app initialization and high-level flow.
- Ensure clear separation of concerns:
    - vision.py: Image processing and ingredient extraction.
    - recipes.py: Recipe generation logic.
    - schemas.py: Data models.
    - validators.py: Logic for validating LLM outputs.
    - ui.py: Streamlit interface components.

## Validation & Error Handling
- Use Pydantic models for all structured data exchange.
- Log a unique request ID for every major operation.
- Implement robust error handling for API calls and file operations.
- Fail fast and provide clear error messages to the UI.
