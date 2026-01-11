# Learning & Exploration Reflection (Part B)

This document captures the learning process, challenges and insights gained while refactoring the recipe helper project to satisfy the Part B “Learning & Exploration Challenge” of the technical assessment.

## Context & Motivation

While I had used **Google Antigravity** in the past for small personal projects, I had not yet used it for a serious, production-style application. This assessment provided the perfect opportunity to deepen that knowledge.

Additionally, this was my **first time using the Gemini 2.0 Flash model**. I wanted to explore it specifically for its **ease of use** in two key areas:
1.  **Unified Multimodal support**: Eliminating the need for separate OCR/vision and text models simplified the architecture significantly.
2.  **Native JSON Output**: The ability to enforce Pydantic schemas via `response_schema` made validation straightforward, avoiding the "retry-parse-fail" loops common with older LLMs.

## Why LangGraph?

I have used LangGraph in previous projects, but I had strictly used its older, linear graph features. I had **not** yet utilized the newer **Human-in-the-Loop (HITL)** capabilities, specifically the `interrupt_before` and functionality.

To satisfy the agent-framework challenge, I refactored the linear pipeline into a stateful graph to test these specific features:

*   **Interrupts**: Pausing the graph to let the user review ingredients *before* generation, and selecting a recipe *before* finalization.
*   **State Persistence**: Using `MemorySaver` to hold the application state while waiting for user input.

* State objects must be fully serialisable. Initially I passed PIL images through the graph state, which produced TypeError: Type is not msgpack serialisable: Image. I resolved this by converting the image to bytes and nulling it after extraction.

* Interrupts must be declared via interrupt\_before when compiling. Otherwise the graph will not pause at intermediate nodes and the UI cannot collect user input.

* The graph state can be updated mid‑execution using graph.update\_state()—essential for injecting preferences or selected recipes from the UI.

## Integrating External Data

Part B encouraged integrating external tools or data. I chose to fetch live weather data and the current time to provide situational context in prompts. Instead of requiring latitude/longitude (as with Open‑Meteo), I used the [wttr.in](https://wttr.in) service, which accepts a city name. This required:

* Studying the wttr.in API documentation to understand the JSON structure. The nested arrays (current\_condition\[0\].weatherDesc\[0\].value) and string fields meant I needed to define Pydantic models (WeatherDesc, CurrentCondition, WeatherResponse) to validate the response before extracting the temperature and description.

* Parsing the current time. I used Python’s pytz library to generate a human‑friendly time string in the Europe/Dublin timezone. Handling time zones correctly was important because naive datetime.now() calls would return the server time, not the user’s locale.

* Summarising the weather. I originally considered using the full forecast, but the Part B guidelines emphasised concise context. I ended up returning a single line such as “It is currently 11 °C and light rain in Dublin at 5 PM.” I created unit tests to ensure the summary works even when fields are missing or the API returns unexpected data.

## UI Refactor

Refactoring the Streamlit UI into a three‑stage flow required understanding how to manage LangGraph within st.session\_state. I learned that:

* The graph object must be stored in the session state along with the current graph state dictionary and a config containing the thread\_id (used by LangGraph for checkpointing).

* Resuming the graph requires passing None as the initial state to graph.stream(); otherwise the graph resets to the beginning.

* Buttons should reset or update parts of the session state to ensure that old results do not leak into new runs.

## Challenges Encountered

* **Serialisation of complex types:** As mentioned, passing non‑serialisable objects (PIL images) through LangGraph caused errors. Converting images to bytes and clearing them after use solved this.

* **State updates:** Initially, I attempted to update the preference and selected recipe directly in the graph state before resuming. However, the graph did not pick up these changes. After consulting the LangGraph API, I learned to use graph.update\_state() with the config and a dict of changes.

* **Time formatting:** Ensuring the time string did not contain leading zeros (e.g., “05 PM”) required a small hack: using strftime("%I %p").lstrip('0').

* **Test adaptation:** The existing tests needed updating to include the new context parameter. I refactored mocks and assertions to account for the weather string and to simulate scenarios where the API call fails.

## Resources Used

* **LangGraph documentation and examples** – understanding how to build and compile a graph, define state and nodes, and manage interruptions.

* **wttr.in documentation and API output samples** – to design the weather models and summary function.

* **Pydantic v2 docs** – for creating nested models and using model\_validate() to ensure strict schema adherence.

* **Tenacity library docs** – for retry strategies and hooks.

* **Pytz library docs** – for timezone conversions.

* **Google Gemini API docs** – verifying that the response\_schema parameter supports arbitrary Pydantic models.

## Insights & Next Steps

* Agent frameworks like LangGraph introduce structure and observability into multi‑step GenAI workflows. They force you to think about state and serialisation, but they make it easier to integrate human feedback loops and resume processes.

* Integrating external data sources requires careful validation and summary. It’s tempting to pass raw JSON into prompts, but distilling it to a few salient features improves reliability.

* If I had more time, I would explore:

* Using asynchronous calls and concurrency for the weather and LLM calls.

* Allowing the user to choose their location dynamically and saving their preferences.

* Caching weather responses to avoid unnecessary API calls and reduce latency.

* Comparing LangGraph with other agent frameworks (e.g. CrewAI) or exploring retrieval‑augmented generation with a recipe database.

This reflection fulfils the documentation requirement for Part B and provides context for team members who want to understand the design choices and lessons learned.

---

