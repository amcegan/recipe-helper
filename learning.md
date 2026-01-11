# Learning & Exploration Reflection 

This document captures the learning process, challenges and insights gained while refactoring the recipe helper project to satisfy the Part B “Learning & Exploration Challenge” of the technical assessment. I also mention what I learned from the Part A challenge though this does go against the instructions given.

## Context & Motivation

While I had used **Google Antigravity** in the past for small personal projects, I had not yet used it for a serious, production-style application. This assessment provided the perfect opportunity to deepen that knowledge.

Additionally, this was my **first time using the Gemini 2.0 Flash model**. I wanted to explore it specifically for its **ease of use** in a fewkey areas:
1.  **Unified Multimodal support**: Eliminating the need for separate OCR/vision and text models simplified the architecture significantly.
2.  **Native JSON Output**: The ability to enforce Pydantic schemas via `response_schema` made validation straightforward, avoiding the "retry-parse-fail" loops common with older LLMs.
3.  **Verify Ease of Use**: Gemini 2.0 Flash is marketed as easy to use, and I wanted to verify.

## Why LangGraph?

I have used LangGraph in previous projects, but I had strictly used its older, linear graph features. I had **not** yet utilized the newer **Human-in-the-Loop (HITL)** capabilities, specifically the `interrupt_before` and functionality.

To satisfy the agent-framework challenge, I refactored the linear pipeline into a stateful graph to test these specific features:

*   **Interrupts**: Pausing the graph to let the user review ingredients *before* generation, and selecting a recipe *before* finalization.
*   **State Persistence**: Using `MemorySaver` to hold the application state while waiting for user input.

* State objects must be fully serialisable. Initially I passed PIL images through the graph state, which produced TypeError: Type is not msgpack serialisable: Image. I resolved this by converting the image to bytes.

* Interrupts must be declared via interrupt\_before when compiling. Otherwise the graph will not pause at intermediate nodes and the UI cannot collect user input.

* The graph state can be updated mid‑execution using graph.update\_state()—essential for injecting preferences or selected recipes from the UI.

## Integrating External Data

Part B encouraged integrating external tools or data. I chose to fetch live weather data and the current time to provide situational context in prompts. Instead of requiring latitude/longitude (as with Open‑Meteo), I used the [wttr.in](https://wttr.in) service, which does not need an API key and accepts a city name; this balances the community nature of the service and lack of an SLA.

## UI Refactor

Refactoring the Streamlit UI into a three‑stage flow required understanding how to manage LangGraph within st.session\_state. I learned that:

* The graph object must be stored in the session state along with the current graph state dictionary and a config containing the thread\_id (used by LangGraph for checkpointing).

* Resuming the graph requires passing None as the initial state to graph.stream(); otherwise the graph resets to the beginning.

* Buttons should reset or update parts of the session state to ensure that old results do not leak into new runs.

## Challenges Encountered

* **Serialisation of complex types:** Passing non‑serialisable objects (PIL images) through LangGraph caused errors. Converting images to bytes and clearing them after use solved this.

* **State updates:** Initially, I attempted to update the preference and selected recipe directly in the graph state before resuming. However, the graph did not pick up these changes. After consulting the LangGraph API, I learned to use graph.update\_state() with the config and a dict of changes.

* **Time formatting:** Ensuring the time string did not contain leading zeros (e.g., “05 PM”) required a small hack: using strftime("%I %p").lstrip('0').

* **Test adaptation:** The existing tests needed updating to include the new context parameter. 

## Insights & Next Steps

* Agent frameworks like LangGraph introduce structure and observability into multi‑step GenAI workflows. They force you to think about state and serialisation, but they make it easier to integrate human feedback loops and resume processes.

* AutoGPT was not used as it was not considered robust enough for most high‑stakes production use.

* CrewAI seemed problematic.CrewAI supports feedback, but it is not designed around deterministic pause/resume of a state graph, which is critical for UI-driven flows like Streamlit.

* I have done alot of work wit RAG in the past and did not think it worth including.

* If I had more time, I would explore prompt chaining.

---

