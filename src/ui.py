"""
Streamlit UI module for the Recipe Helper application.
Handles file uploads, user interaction, and manages the LangGraph execution flow.
"""
import streamlit as st
import uuid
import asyncio
from PIL import Image
from src.vision import VisionPipeline
from src.recipes import RecipePipeline
from src.logger import get_request_logger, setup_logger, log_entry_exit
from src.executor import run_cpu_bound
from src.config import settings
from src.graph import create_recipe_graph, get_initial_state, update_user_preference, update_selected_recipe
from src.security import safe_error_message

def image_to_bytes(img):
    """
    Helper for multiprocessing image conversion.
    Converts a PIL Image to PNG bytes.

    Args:
        img (Image.Image): The PIL Image to convert.

    Returns:
        bytes: The image data in PNG format.
    """
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

async def run_graph(graph, inputs, config, state_ref):
    """
    Helper to run the graph asynchronously and update state.
    Iterates through graph events and merges results into a reference dictionary.

    Args:
        graph (CompiledGraph): The compiled LangGraph workflow.
        inputs (dict or None): Initial inputs for the graph, or None when resuming.
        config (dict): Configuration for the graph run (e.g., thread_id).
        state_ref (dict): A reference to the state dictionary to update with results.
    """
    try:
        async for event in graph.astream(inputs, config):
            node_name = next(iter(event))
            state_ref.update(event[node_name])
    except Exception as e:
        st.error(f"Graph Error: {safe_error_message(e)}")

@log_entry_exit
def render_ui():
    """
    Main function to render the Streamlit UI.
    Sets up page config, manages session state, and handles the multi-step recipe generation workflow.
    """
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
        st.session_state.graph_state = get_initial_state(request_id)

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
        ingredients = st.session_state.graph_state.get("ingredients") or []
        for ing in ingredients:
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
                update_user_preference(
                    st.session_state.graph,
                    st.session_state.config,
                    pref
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
                update_selected_recipe(
                    st.session_state.graph,
                    st.session_state.config,
                    chosen_title
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
        recipe_ingredients = recipe.ingredients or []
        for item in recipe_ingredients:
            st.write(f"- {item}")
        st.info(f"**Cooking Time:** {recipe.cooking_time}")

        st.subheader("Instructions")
        recipe_steps = recipe.steps or []
        for i, step in enumerate(recipe_steps, 1):
            st.write(f"{i}. {step}")
        
        if recipe.notes:
            st.subheader("Chef's Notes")
            st.write(recipe.notes)
    

