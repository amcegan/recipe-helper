# Project Creation Prompt: Recipe Helper

You are building a modular, production-ready Python application that recommends recipes based on photos of ingredients. The objective is to demonstrate professional software engineering standards, including separation of concerns, strict data validation, robust error handling, and comprehensive documentation for both humans and AI agents.

## High-Level Requirements

1. **Streamlit User Interface**
    *   **Single-Column Layout**: A clean, modern interface for mobile and desktop.
    *   **Flow**: Upload image → Detect ingredients (with confidence scores) → Select recipe suggestion → Generate final detailed recipe.
    *   **Resource Safety**: Use context managers (`with PIL.Image.open(...)`) for all image/file handling to prevent memory leaks.

2. **Vision Pipeline (Gemini API)**
    *   **Model**: Use `gemini-2.0-flash` for multi-modal analysis.
    *   **Thresholding**: Implement `INGREDIENT_CONFIDENCE_THRESHOLD` (env variable, default 0.5) to filter out low-certainty detections.
    *   **Structured Output**: Leverage Gemini's native JSON mode with Pydantic schemas.

3. **Recipe Generation Pipeline**
    *   **Flow**: Multi-step generation (Suggestions → Final Recipe).
    *   **Context**: Ensure preferences (e.g., "vegetarian", "spicy") are strictly adhered to.
    *   **Safety**: Prohibit harmful suggestions (e.g., unknown mushrooms) and unrequested cooking methods (e.g., naked-flame barbecues).

4. **Modular Architecture**
    *   **Modules**: `vision.py`, `recipes.py`, `ui.py`, `schemas.py`, `validators.py`, `exceptions.py`.
    *   **Library Design**: Components in `src/` must be decoupled from UI logic for reusability.
    *   **Exceptions**: Use a domain-specific exception hierarchy (e.g., `AppVisionError`, `AppValidationError`).

5. **Validation & Reliability**
    *   **Pydantic**: Enforce strict validation on all AI outputs immediately after parsing using `Model.model_validate()`.
    *   **Retries**: Decorate all service methods with `tenacity` retries (exponential backoff).
    *   **Logging**: Implement a specialized logger that injects a unique `request_id` into every log message for session traceability.

## Prompting Strategy & Guardrails

### Ingredient Extraction
*   **Role**: "You are an expert ingredient-extraction engine."
*   **Return**: JSON object mapping to `IngredientList` schema (name, confidence, notes).
*   **Rules**: No speculation—label uncertain items as "unknown". No inferred items or brands. Culinary context only.

### Recipe Suggestions
*   **Role**: "You are a professional chef and nutritionist."
*   **Return**: JSON object mapping to `RecipeSuggestionList` schema.
*   **Rules**: Clearly distinguish between available and missing ingredients. Explain rationale. professional and child-friendly language.

## Antigravity Configuration (AI Agents)

*   **Instruction Discovery**: Store AI-specific project guidelines in `.agent/Agents.md`.
*   **Rules & Workflows**: 
    *   Maintain `.agent/rules/python-standards.md` for style and modularity enforcement.
    - Define a `generate-unit-tests` workflow in `.agent/workflows/`.
*   **Documentation Map**: Maintain a table in `README.md` mapping all `.md` files to their audience and purpose.

## Security & Privacy
*   **Secret Management**: Use `.env.example` as a template; never commit hardcoded keys. Provide guidance for Production Secret Management (GitHub/AWS/Google).
*   **Confinement**: Restrict file I/O to the project workspace.
*   **API Security**: Set `max_output_tokens`, `temperature`, and `safety_settings` for all model interactions.

## Development Workflow
1.  **Plan**: Present module outlines and schemas for approval.
2.  **Scaffold**: Generate skeletons following PEP 8 and type hints.
3.  **Implement**: Build core pipelines with retries, logging, and validation.
4.  **Test**: Comprehensive unit testing with `pytest`, mocking all external Gemini calls.
5.  **Document**: Deliver final guides in `README.md` and `.agent/Agents.md`.

## Development Guidelines

- **Clean Code**: Use well-named variables and functions that clearly convey intent.
- **Modularity**: Externalize all LLM prompts to a dedicated `prompts.py` module.
- **Resilience**: Implement `tenacity` retries for all service calls. Ensure the logger captures specific error codes (e.g., 429, 503) during retry attempts.
- **Resource Management**: Always use context managers (`with` statements) to ensure resources like files and images are properly closed.
- **Model Configuration**: Explicitly set token limits, temperature, and safety settings for every model call.
- **Integrity**: Verify that all response elements are valid against Pydantic models immediately upon receipt.
- **Interface Design**: Ensure others can reuse portions of the codebase with confidence in the correctness and reliability of the results.
- **Interface Design**: Use a domain-specific exception hierarchy.


