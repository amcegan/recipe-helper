# Recipe Helper - AI Assisted Development

## Build and Run Commands
- Start Streamlit app: `streamlit run main.py`
- Run unit tests: `pytest tests/`
- Install dependencies: `pip install -r requirements.txt`

## Design Decisions
- **Modularity**: Business logic is separated into `src/` modules. `main.py` is kept minimal.
- **Validation**: Pydantic models are used to ensure LLM outputs strictly follow the expected format.
- **Logging**: A custom `RequestLoggerAdapter` is used to include a unique `request_id` in every log message, facilitating easier debugging of specific user sessions.
- **Safe Prompting**: Integrated guardrails in LLM prompts to prevent hallucination, prioritize safety, and ensure culinary context.

## External Documentation References
- [Google Gemini API Docs](https://ai.google.dev/docs)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
