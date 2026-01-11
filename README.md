# Recipe Helper – AI‑Powered Recipe Recommendation System
This project was created using Google's AntiGravity AI agent. An agents.md file can be found in the .agent directory.
The full project prompt can be found in [project-prompt.md](project-prompt.md).

Recipe Helper is an AI-powered culinary companion that transforms photos of your ingredients into delicious recipes.

It demonstrates an end‑to‑end workflow using a vision‑capable large language model to extract ingredients from an image, reason about how the ingredients fit together, and synthesise an easy‑to‑follow recipe tailored to the user's preferences. The project emphasises safety, reliability and clear separation of concerns so that the core services can be reused as a library or extended for future work.

## Project Documentation

| File | Audience | Purpose |
| :--- | :--- | :--- |
| **[README.md](README.md)** | Users / Devs | Primary project overview, setup, and execution guide. |
| **[project-prompt.md](project-prompt.md)**| Devs | Comprehensive blueprint for recreating this project from scratch. |
| **[.agent/agents.md](.agent/agents.md)** | AI Assistants | Agent Context, architectural constraints, safety standards, and coding conventions for AI. |
| **[.agent/rules/python-standards.md](.agent/rules/python-standards.md)** | Devs / AI | Specific coding standards and best practices for Python. |
| **[.agent/workflows/generate-unit-tests.md](.agent/workflows/generate-unit-tests.md)** | Devs / AI |  Generate/Run unit tests for the project. |

## Project Overview

At a high level the application operates in three stages:

1. **Ingredient extraction** – A multi‑modal model (gemini‑2.0‑flash) analyses the uploaded image and returns a structured list of ingredients with confidence scores. Validation via Pydantic models ensures that the AI output conforms to the expected schema and that low‑confidence detections can be filtered out using an environment variable.

2. **Recipe suggestion** – Given the extracted ingredients and an optional natural‑language user preference (for example, “quick vegetarian lunch”), a text model suggests 3–5 recipe ideas. Each suggestion contains a title, diet tags, required/missing ingredients, estimated prep time, and a rationale explaining why the recipe matches the preference.

3. **Final recipe generation** – After the user selects one of the suggestions, the model produces a detailed step‑by‑step recipe that includes ingredients, instructions, cooking time and any chef’s notes. This final step again validates the AI output against a strict schema to prevent hallucinated or malformed responses.

Throughout the workflow the application uses a unique request\_id and consistent logging to trace operations. Retries via the tenacity library wrap all external API calls to recover gracefully from transient network errors or empty model responses.

## Architectural Design & Decisions

The project is organised as a small library with a thin Streamlit user interface. This separation makes it easy to test and reuse the business logic without depending on the UI framework.

* **Modular services and components:**

  * **src/vision.py** encapsulates all image handling and calls to the Gemini vision API. It accepts a PIL Image, constructs a prompt, and returns a IngredientList Pydantic model after filtering by confidence.

  * **src/recipes.py** contains the recipe pipeline. It exposes two methods – **suggest\_recipes()** for high‑level suggestions and **generate\_final\_recipe()** for the full recipe – both of which enforce schema validation and implement exponential backoff retries.

  * **src/prompts.py** centralises all prompts. Having the text in one place consistent prompt engineering.

  * **src/schemas.py** defines strong Pydantic models for ingredients, suggestions and final recipes. These models provide type safety, allow downstream code to reason about AI output, and support response\_schema integration with the Gemini API.

  * src/validators.py offers generic JSON cleaning/validation and a reusable retry wrapper for calls that may intermittently return invalid JSON. The retry logic is separate from tenacity to allow explicit recovery from schema‑related issues.

  * src/logger.py sets up a structured logger and exposes get\_request\_logger() and log\_retry() so that every log line includes a request identifier. This aids debugging when multiple users are interacting concurrently.

  * src/exceptions.py defines a clear exception hierarchy (AppVisionError, AppRecipeError, AppValidationError) which surfaces meaningful error messages to the caller without leaking implementation details.

* **Streamlit front‑end:** The src/ui.py module implements the user interface. It uses Streamlit to render a three‑stage experience: uploading an image, reviewing detected ingredients, and generating recipes. The UI stores intermediate results (ingredients, suggestions, final\_recipe) in st.session\_state and passes the user’s textual preference from a st.text\_input() field to the recipe pipeline. Errors are handled gracefully via status messages, and each stage can be retried without refreshing the page.

* **Configuration via environment:** Sensitive data such as the Gemini API key are loaded from a .env file using python‑dotenv. Optional settings (LOG\_LEVEL, INGREDIENT\_CONFIDENCE\_THRESHOLD) allow you to tune logging verbosity and filter out low‑confidence ingredients without changing the source code.

* **Testing:** The tests/ folder contains unit tests for the vision and recipe pipelines and for the generic validators. Tests use pytest and unittest.mock to mock out external API calls so that they can run offline. The tests demonstrate success paths, error handling and retry behaviour.

### Trade‑offs and Rationale

* **Gemini vs. other models:** Google’s gemini‑2.0‑flash was chosen because it offers integrated multi‑modal support and native structured JSON output via the response\_schema parameter. This reduces prompt engineering overhead and simplifies validation compared with raw text‑only models.

* **Streamlit UI:** Streamlit provides a rapid way to build interactive web apps with minimal boilerplate. It is not production‑optimised but suits the goal of demonstrating the core GenAI workflow. By keeping the UI thin, it’s straightforward to replace with a CLI or REST API if needed.

* **Schema enforcement with Pydantic:** Validating AI responses against Pydantic models prevents downstream crashes and surfaces issues early. It also allows us to use response\_schema on the Gemini client, which requests the model to emit JSON conforming to our schema. This approach mitigates hallucination and ensures contract‑driven development.

* **Retries and logging:** Transient API failures are common when calling large models. Using tenacity with exponential backoff and a retry limit provides resilience while preventing infinite loops. Including the request\_id in logs enables correlation across services and is a pattern adopted in many production systems.

## Setup Instructions

### Prerequisites

1. **Python 3.9+**
2. **Google Gemini API Key**

### Setup

1. **Create and activate a virtual environment** (recommended):

   python3 \-m venv venv  
   source venv/bin/activate  \# or \`venv\\Scripts\\activate\` on Windows

2. **Install dependencies**:

   pip install \--upgrade pip  
   pip install \-r requirements.txt

3. **Configure environment variables**:

   Copy .env.example to .env and set the following keys:

   * GEMINI\_API\_KEY: your Google Gemini API key. You can obtain one from [Google AI Studio](https://aistudio.google.com/).

   * LOG\_LEVEL (optional): set to DEBUG for verbose logs or INFO for typical output.

   * INGREDIENT\_CONFIDENCE\_THRESHOLD (optional): float between 0.0 and 1.0 to filter low‑confidence detections. Default is 0.5.

The application reads these values at runtime using python‑dotenv. **Never commit your API key to version control.**

## Running the Application

Start the Streamlit server from the project root:

streamlit run main.py

If it doesn't open automatically, wait for the local URL (usually `http://localhost:8501`) to appear and open it in your browser.
 The flow is:

1. Upload an image of your ingredients (supported formats: PNG/JPG).

2. Click **Detect Ingredients**. The application calls the vision pipeline and displays each ingredient with a colour‑coded confidence indicator.

3. Enter an optional preference (for example, “quick vegetarian lunch”) in the text input field. Click **Generate Recipe Suggestions** to receive 3–5 ideas tailored to your ingredients and preferences.

4. Choose one of the suggestions from the dropdown and click **Get Final Recipe** to view a complete recipe with ingredients, instructions, cooking time and notes.

If the app cannot find your API key or encounters an error, an informative message will be displayed. Check your .env configuration and logs for details.

## Running Tests

The project includes unit tests covering the core pipelines and validators. To execute the tests, run:

pytest tests/

The tests use mocking to simulate API responses and therefore do not require an internet connection or a valid API key. They verify success paths, error handling, retries and confidence filtering.

## Technology Choices

| Technology | Role | Rationale |
| :---- | :---- | :---- |
| **Gemini 2.0 Flash** | Vision & text LLM | Native multi‑modal support with response\_schema for structured JSON output and low latency. |
| **Streamlit** | UI framework | Simplifies building interactive Python apps without HTML/JS; ideal for demo purposes. |
| **Pydantic v2** | Data validation & typing | Ensures AI responses conform to expected schemas; reduces runtime errors and simplifies downstream code. |
| **Tenacity** | Retry logic | Provides exponential backoff and hooks for logging; essential for production‑grade API resilience. |
| **Pillow (PIL)** | Image handling | Lightweight and robust library for reading various image formats. |
| **Python‑Dotenv** | Secret management | Loads environment variables from a .env file; avoids hard‑coding secrets. |

## Limitations & Future Improvements

* **LLM dependency and cost:** The quality of the output depends on the underlying Gemini model and may change over time. Running the model requires an API key and may incur costs.

* **No persistence:** All state is held in memory via Streamlit’s session. In a production system you might persist previous sessions, user feedback or favourite recipes.

* **Scalability:** Streamlit is single‑process and not suitable for high‑traffic environments. To scale, the service layer (VisionPipeline and RecipePipeline) could be exposed via a REST or gRPC API behind a load balancer, and the UI moved to a separate front‑end.

## Edge Case Handling & Robustness

The assessment requires demonstrating how the system handles failures and edge cases. This implementation addresses several robustness scenarios:

1.  **External API Failure (Weather)**: The `get_weather_context` function uses a `try-except` block. If `wttr.in` is unreachable or returns invalid data, the system gracefully degrades to a "mild weather" default rather than crashing the entire recipe flow.
2.  **Transient Network Errors**: All Gemini API calls in `src/vision.py` and `src/recipes.py` are wrapped with the `@retry` decorator from the `tenacity` library. This handles temporary hiccups (like rate limits or timeouts) by automatically retrying with exponential backoff.
3.  **Low-Confidence Detections**: The vision pipeline implements a filter (`INGREDIENT_CONFIDENCE_THRESHOLD`) to silently discard hallucinations or uncertain ingredients, ensuring only high-quality data reaches the recipe generator.
4.  **LLM Output Validation**: We do not blindly trust the AI. Every response is parsed and immediately validated against Pydantic models. If the schema doesn't match, an `AppValidationError` is raised immediately, preventing "silent failures" downstream.
5.  **Graph State Serialization**: To prevent the "Un-serializable Data" edge case common in distributed graphs, the `extract_ingredients_node` enforces that images are strictly converted to `bytes` and then cleared (`None`) after processing to keep checkpoints lightweight.

## Production Deployment Considerations

To transition this proof-of-concept into a production-grade service, the following architectural changes would be required:

1.  **State Persistence**: Replace the in-memory `MemorySaver` with a durable backend like **PostgreSQL** (using `AsyncPostgresSaver`) or Redis. This ensures user sessions survive service restarts and allows for horizontal scaling.
2.  **Scalable Serving**: Decouple the Streamlit UI from the core logic. Deploy the LangGraph application as a **FastAPI** microservice (using LangServe) to handle high concurrency and provide a clean REST API for multiple front-ends (web, mobile).
3.  **Time & Localization**: Remove reliance on server system time. Use the user's browser/client to send their local timezone or geolocation for accurate time and weather context.
4.  **Weather Service SLA**: Replace the community-hosted `wttr.in` with a commercial provider (e.g., OpenWeatherMap or Google Maps Platform) to guarantee uptime and latency SLAs.
5.  **Observability**: Integrate structured logging (e.g., OpenTelemetry) to trace requests across the graph nodes and monitor LLM latency/costs in real-time.

---