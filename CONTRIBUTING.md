# Contributing to Recipe Helper

Thank you for your interest in contributing to Recipe Helper! This project follows strict professional coding standards and AI-assisted development practices.

## Coding Standards

All Python code must adhere to the following standards:
- **PEP 8**: Follow standard Python style guidelines.
- **Type Hinting**: Mandatory for all function arguments and return values.
- **Documentation**: Every public module, class, and function must have a docstring (following [Google-style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) format).
- **Naming**: `snake_case` for variables/functions, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants.
- **Resource Management**: Use context managers (`with`) for file and image operations.
- **Modularity**: Business logic must reside in `src/`, while `ui.py` is reserved for presentation logic.

For more details, see [.agent/rules/python-standards.md](.agent/rules/python-standards.md).

## AI Agent Conventions

If you are using an AI assistant (like Google Antigravity) to contribute:
- **Safety**: Ensure all LLM calls include safety settings.
- **Validation**: Enforce schema validation using Pydantic models.
- **Logging**: Use the project's structured logging with unique request IDs.
- **Fail Fast**: Implement validation that catches configuration errors on startup.

For more details, see [.agent/Agents.md](.agent/Agents.md).

## Development Workflow

1.  **Environment Setup**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
2.  **Testing**:
    - Every new feature must have corresponding tests in the `tests/` directory.
    - Run the suite using `pytest tests/`.
3.  **Logging & Tracing**: Every major operation should include a unique `request_id` for request-based log aggregation.
4.  **Branching**: Use descriptive branch names and submit PRs with clear explanations of changes.

## Security

- Never log or display raw API keys or secrets.
- Use the `mask_secrets` utility in `src/security.py` for all logs and error messages.
