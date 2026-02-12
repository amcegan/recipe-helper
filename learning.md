# Learning & Exploration Reflection 

This document captures the learning process, challenges, and insights gained while refactoring the Recipe Helper project into a stateful **LangGraph** flow using **Google Antigravity**.

## Google Antigravity

While I had used **Google Antigravity** in the past month for small personal projects, I had not yet used it for a serious, production-style application. This project provided the perfect opportunity to deepen that knowledge.
Antigravity is an excellent tool for code generation and refactoring. Any issues I had were due to poor prompting on my behalf; I would highly recommend.
Antigravity was excellent in solving the bugs/issue (see: Challenges Encountered section), providing excellent educational feedback on the code and refactoring suggestions that I just had to accept. Antigravity provides a full markdown report of the changes it made, which is very helpful for learning.

## Gemini 2.0 Flash

Additionally, this was my first time using the Gemini 2.0 Flash model. I wanted to explore it specifically for its **ease of use** in a few key areas:
1.  **Unified Multimodal support**: Eliminating the need for separate OCR/vision and text models simplified the architecture significantly.
2.  **Native JSON Output**: The ability to enforce Pydantic schemas via `response_schema` made validation straightforward, avoiding the "retry-parse-fail" loops common with older LLMs.
3.  **Verify Ease of Use**: Gemini 2.0 Flash is marketed as easy to use, and I wanted to verify.

## Why LangGraph?

I have used LangGraph in previous projects, but I had strictly used its older version, for multi-step workflows. I had **not** yet utilized the newer **Human-in-the-Loop (HITL)** capabilities, which unsurprisingly needs a UI. It was a great learning experience as I had not foreseen the complexity it necessarily brought to the UI code.

To explore agent-style orchestration, I refactored the linear pipeline into a stateful graph. As well as the aforementioned UI learnings, the other features/experiences worth mentioning are:

*   **Interrupts**: Pausing the graph to let the user review ingredients *before* generation, and selecting a recipe *before* finalization.
*   **State Persistence**: Using `MemorySaver` to hold the application state while waiting for user input.

* State objects must be fully serialisable. Initially I passed PIL images through the graph state, which produced TypeError: Type is not msgpack serialisable: Image. I resolved this by converting the image to bytes.

* Interrupts must be declared via interrupt\_before when compiling. Otherwise the graph will not pause at intermediate nodes and the UI cannot collect user input.

* The graph state can be updated mid‑execution using graph.update\_state()—essential for injecting preferences or selected recipes from the UI.


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

* CrewAI seemed problematic. CrewAI supports feedback, but it is not designed around deterministic pause/resume of a state graph, which is critical for UI-driven flows like Streamlit.

* I have done a lot of work with RAG in the past and did not think it worth including.

* It would be beneficial to cache the weather responses.

* If I had more time, I would demonstrate prompt chaining using either
    - A. Two‑stage suggestion generation: Use an initial prompt to brainstorm a larger set of recipe ideas (say, 10–15 titles) based on the ingredients and context. Feed those titles into a second prompt that ranks them or filters them against user preferences and dietary constraints, returning only the top 3–5 suggestions with rationales. This makes the selection more controllable and lets you inspect the ranking logic.
    - B. Recipe quality check: After generating a final recipe, run a follow‑up prompt that reviews the recipe for clarity, completeness and safety (for example, checking that all steps use available ingredients and that cooking times are consistent). If issues are detected, the chain could trigger a regeneration or adjust the instructions.

---

