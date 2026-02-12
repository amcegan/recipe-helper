# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Sanitized Input**: Implemented `sanitize_input` in `src/security.py` to prevent prompt injection by cleaning user-provided strings (truncation, keyword redaction, delimiter escaping).
- **Generalized Secret Masking**: Updated `mask_secrets` to automatically detect and redact any sensitive fields defined in application settings.
- **Formally Documented Contribution Standards**: Added `CONTRIBUTING.md` and referenced internal standards in `README.md`.
- **State management helpers**: Added `get_initial_state`, `update_user_preference`, and `update_selected_recipe` to `src/graph.py` to encapsulate state transitions.

### Changed
- **Concurrency Model Simplification**: Replaced Dask and Distributed dependencies with Python's standard `concurrent.futures.ProcessPoolExecutor` for lighter, more reliable local execution.
- **Safe Logging**: Enhanced `log_entry_exit` decorator to support asynchronous functions and enforced error message sanitization using `safe_error_message`.
- **Project Reframing**: Updated `README.md` and `LEARNING.md` to frame the project as a technical experiment in AI-assisted development (Antigravity) and LangGraph refactoring.

## [1.1.0] - 2026-02-12

### Added
- **LangGraph Orchestration**: Refactored the core pipeline into a stateful graph in `src/graph.py` with 5 nodes:
  - Extract Ingredients
  - Check Weather & Time
  - Suggest Recipes (Interrupt)
  - Human Review (Interrupt)
  - Generate Final Recipe
- **Situational Context**: Integrated weather data (via `wttr.in`) and current Dublin time into LLM prompts for context-aware recipe suggestions.
- **Structured Logging**: Implemented JSON logging with `structlog` and session-based `request_id` tracking.
- **Fail-Fast Configuration**: Added `pydantic-settings` for type-safe environment variable management.

## [1.0.0] - 2026-02-01

### Added
- **Vision Pipeline**: Core logic for extracting ingredients from images using Gemini 2.0 Flash.
- **Recipe Generation**: Pipeline for generating recipe ideas and detailed expands based on ingredient lists.
- **Streamlit UI**: Initial interactive interface for image uploads and recipe display.
- **Comprehensive Testing**: Initial test suite for vision and recipe logic.
