# Recipe Helper

Recipe Helper is an AI-powered culinary companion that transforms photos of your ingredients into delicious recipes. 
Using Google's Gemini 2.0 Flash model, the application detects ingredients with high precision and suggests creative, safe, and personalized recipes.

## Overview & Architecture

The application is built with a modular, "safety-first" architecture designed for production reliability:

-   **Modular Design**: Business logic is decoupled into specialized modules (`vision.py`, `recipes.py`, `validators.py`).
-   **Schema Enforcement**: All AI outputs are strictly validated against Pydantic models to ensure data integrity and prevent hallucination.
-   **Reliability Layer**: Every external API call is protected by exponential backoff retries (`tenacity`) and proactive error logging.
-   **Centralized Prompts**: LLM instructions are managed in a single `prompts.py` file for consistent AI behavior and easy calibration.
-   **Traceability**: A custom logging adapter injects unique `request_id`s into every log message, facilitating easy debugging of specific user sessions.

## Setup Instructions

### 1. Prerequisites
- Python 3.9+ 
- A Google Gemini API Key

### 2. Environment Configuration
Copy the .env.example file to .env and set your API key:
Edit `.env` and set:
- `GEMINI_API_KEY`: Your key from [Google AI Studio](https://aistudio.google.com/). A paid account is recommended.
- `LOG_LEVEL`: (Optional) Set to `DEBUG` for detailed trace logs or `INFO` for standard output.

### 3. Dependency Installation
We recommend using a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## How to Run

### Start the Application
Run the Streamlit server from the project root:
```bash
streamlit run main.py
```
Wait for the local URL (usually `http://localhost:8501`) to appear and open it in your browser.

### Run Tests
The project includes a comprehensive suite of unit tests covering vision, recipes, and utility logic:
```bash
./venv/bin/python3 -m pytest tests/
```

## Technology Choices

| Technology | Purpose | Why? |
| :--- | :--- | :--- |
| **Gemini 2.0 Flash** | Core AI | Multi-modal performance with native structured output (JSON) and low latency. |
| **Streamlit** | UI Framework | Allows for rapid development of interactive, data-driven web interfaces using only Python. |
| **Pydantic v2** | Data Validation | Industry standard for type enforcement and JSON serialization, crucial for reliable LLM integration. |
| **Tenacity** | Retry Logic | Highly configurable decorator-based retries to handle transient network or API errors gracefully. |
| **Pillow** | Image Processing | Robust and lightweight library for handling various image formats before AI analysis. |
| **Python-Dotenv** | Secret Management | Securely loads configuration and credentials from a local environment file. |


