import streamlit as st
import uuid
from PIL import Image
from src.vision import VisionPipeline
from src.recipes import RecipePipeline
from src.logger import get_request_logger
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from src.graph import create_recipe_graph

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

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        st.error("Missing GEMINI_API_KEY environment variable. Please set it in your .env file.")
        return

    st.header("1. Upload Ingredients")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        with Image.open(uploaded_file) as image:
            st.image(image, caption="Uploaded Image", width="stretch")
            
            # Convert PIL Image to bytes for LangGraph serialization
            import io
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            st.session_state.graph_state["image"] = buf.getvalue()

            if st.button("Detect Ingredients"):
                # Reset state for new run
                st.session_state.graph_state["ingredients"] = None
                st.session_state.graph_state["suggestions"] = None
                st.session_state.graph_state["final_recipe"] = None
                st.session_state.graph_state["error"] = None
                
                # Start the graph
                with st.spinner("Analyzing ingredients and checking weather..."):
                    try:
                        for event in st.session_state.graph.stream(
                            st.session_state.graph_state,
                            st.session_state.config
                        ):
                            node_name = next(iter(event))
                            st.session_state.graph_state.update(event[node_name])
                    except Exception as e:
                        st.error(f"Graph Initialization Error: {e}")

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
                
                try:
                    for event in st.session_state.graph.stream(
                        None, # Resuming
                        st.session_state.config
                    ):
                        node_name = next(iter(event))
                        st.session_state.graph_state.update(event[node_name])
                except Exception as e:
                    st.error(f"Graph Resumption Error (Suggestions): {e}")

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
                
                try:
                    for event in st.session_state.graph.stream(
                        None, # Resuming
                        st.session_state.config
                    ):
                        node_name = next(iter(event))
                        st.session_state.graph_state.update(event[node_name])
                except Exception as e:
                    st.error(f"Graph Resumption Error (Final): {e}")

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
