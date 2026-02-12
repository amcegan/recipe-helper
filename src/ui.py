import streamlit as st
import uuid
import asyncio
from PIL import Image
from src.vision import VisionPipeline
from src.recipes import RecipePipeline
from src.logger import get_request_logger
from src.executor import run_cpu_bound
from src.config import settings
from src.graph import create_recipe_graph
from src.security import safe_error_message

def image_to_bytes(img):
    """Helper for multiprocessing image conversion."""
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

async def run_graph(graph, inputs, config, state_ref):
    """Helper to run the graph asynchronously and update state."""
    try:
        async for event in graph.astream(inputs, config):
            node_name = next(iter(event))
            state_ref.update(event[node_name])
    except Exception as e:
        st.error(f"Graph Error: {safe_error_message(e)}")

def render_ui():
    st.set_page_config(page_title="Recipe Helper", page_icon="🍳", layout="wide")
    
    st.title("🍳 Recipe Helper")
    st.markdown("Upload a photo of your ingredients and get personalized recipes based on the current weather and time!")

    if "request_id" not in st.session_state:
        st.session_state.request_id = str(uuid.uuid4())[:8]
    
    request_id = st.session_state.request_id
    logger = get_request_logger(request_id)
    
    if "graph" not in st.session_state:
        st.session_state.graph = create_recipe_graph()
        st.session_state.config = {"configurable": {"thread_id": request_id}}
        st.session_state.graph_state = {
            "image": None,
            "ingredients": None,
            "context": None,
            "suggestions": None,
            "selected_recipe": None,
            "user_preference": "",
            "final_recipe": None,
            "request_id": request_id,
            "error": None
        }

    # API Key is validated by Pydantic on Settings instantiation.
    # If it's missing, the app will fail to start-up with a clear error.

    st.header("1. Upload Ingredients")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        with Image.open(uploaded_file) as image:
            st.image(image, caption="Uploaded Image", width="stretch")
            
            st.session_state.graph_state["image"] = asyncio.run(run_cpu_bound(image_to_bytes, image))

            if st.button("Detect Ingredients"):
                # Reset state for new run
                st.session_state.graph_state["ingredients"] = None
                st.session_state.graph_state["suggestions"] = None
                st.session_state.graph_state["final_recipe"] = None
                st.session_state.graph_state["error"] = None
                
                # Start the graph
                with st.spinner("Analyzing ingredients and checking weather..."):
                    asyncio.run(run_graph(
                        st.session_state.graph,
                        st.session_state.graph_state,
                        st.session_state.config,
                        st.session_state.graph_state
                    ))

    # Display Context and Ingredients
    if st.session_state.graph_state.get("context"):
        st.info(f"🌍 **Context:** {st.session_state.graph_state['context']}")

    if st.session_state.graph_state.get("ingredients"):
        st.divider()
        st.header("2. Detected Ingredients")
        for ing in st.session_state.graph_state["ingredients"]:
            confidence_color = "green" if ing.confidence > 0.8 else "orange" if ing.confidence > 0.5 else "red"
            st.markdown(f"- **{ing.name}** (Confidence: :{confidence_color}[{ing.confidence:.2f}])")

        st.text_input(
            "Any preferences? (e.g., 'quick vegetarian lunch')", 
            key="pref_input",
            value=st.session_state.graph_state["user_preference"]
        )

        if st.button("Generate Recipe Suggestions"):
            with st.spinner("Thinking of recipes..."):
                # Update preference and resume graph
                pref = st.session_state.pref_input
                st.session_state.graph.update_state(
                    st.session_state.config,
                    {"user_preference": pref}
                )
                
                asyncio.run(run_graph(
                    st.session_state.graph,
                    None, # Resuming
                    st.session_state.config,
                    st.session_state.graph_state
                ))

    # Display Suggestions and Recipe Selection
    if st.session_state.graph_state.get("suggestions"):
        st.divider()
        st.header("3. Recipe Suggestions")
        
        suggestions = st.session_state.graph_state["suggestions"]
        selected_titles = [s.title for s in suggestions]
        chosen_title = st.selectbox("Choose a recipe to see details:", selected_titles)
        
        if st.button("Get Final Recipe"):
            with st.spinner("Preparing detailed recipe..."):
                # Update selection and resume graph
                st.session_state.graph.update_state(
                    st.session_state.config,
                    {"selected_recipe": chosen_title}
                )
                
                asyncio.run(run_graph(
                    st.session_state.graph,
                    None, # Resuming
                    st.session_state.config,
                    st.session_state.graph_state
                ))

    # Final Recipe Display
    if st.session_state.graph_state.get("final_recipe"):
        st.divider()
        recipe = st.session_state.graph_state["final_recipe"]
        st.header(f"📖 Final Recipe: {recipe.title}")
        
        st.subheader("Ingredients")
        for item in recipe.ingredients:
            st.write(f"- {item}")
        st.info(f"**Cooking Time:** {recipe.cooking_time}")

        st.subheader("Instructions")
        for i, step in enumerate(recipe.steps, 1):
            st.write(f"{i}. {step}")
        
        if recipe.notes:
            st.subheader("Chef's Notes")
            st.write(recipe.notes)
    
    logger.debug("EXITING: render_ui")
