import streamlit as st
import uuid
from PIL import Image
from src.vision import VisionPipeline
from src.recipes import RecipePipeline
from src.logger import get_request_logger
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def render_ui():
    st.set_page_config(page_title="Recipe Helper", page_icon="🍳", layout="wide")
    
    st.title("🍳 Recipe Helper")
    st.markdown("Upload a photo of your ingredients and get professional recipe recommendations!")

    if "request_id" not in st.session_state:
        st.session_state.request_id = str(uuid.uuid4())[:8]
    
    request_id = st.session_state.request_id
    logger = get_request_logger(request_id)
    logger.debug(f"ENTERING: render_ui with request_id={request_id}")

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        st.error("Missing GEMINI_API_KEY environment variable. Please set it in your .env file.")
        st.info("You can get an API key from [Google AI Studio](https://aistudio.google.com/).")
        return

    vision_pipeline = VisionPipeline(api_key)
    recipe_pipeline = RecipePipeline(api_key)

    st.header("1. Upload Ingredients")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        with Image.open(uploaded_file) as image:
            st.image(image, caption="Uploaded Image", width='content')

            if st.button("Detect Ingredients"):
                with st.spinner("Analyzing image..."):
                    try:
                        ingredients = vision_pipeline.extract_ingredients(image, request_id)
                        st.session_state.ingredients = ingredients.ingredients
                        st.success(f"Detected {len(ingredients.ingredients)} ingredients!")
                    except Exception as e:
                        st.error(f"Error extracting ingredients: {e}")

    if "ingredients" in st.session_state:
        st.divider()
        st.header("2. Detected Ingredients")
        for ing in st.session_state.ingredients:
            confidence_color = "green" if ing.confidence > 0.8 else "orange" if ing.confidence > 0.5 else "red"
            st.markdown(f"- **{ing.name}** (Confidence: :{confidence_color}[{ing.confidence:.2f}])")
            if ing.notes:
                st.caption(f"Note: {ing.notes}")

        user_preference = st.text_input("Any preferences? (e.g., 'quick vegetarian lunch')", "")

        if st.button("Generate Recipe Suggestions"):
            with st.spinner("Thinking of recipes..."):
                try:
                    suggestions = recipe_pipeline.suggest_recipes(
                        st.session_state.ingredients, 
                        user_preference, 
                        request_id
                    )
                    st.session_state.suggestions = suggestions.suggestions
                except Exception as e:
                    st.error(f"Error generating suggestions: {e}")

    if "suggestions" in st.session_state:
        st.divider()
        st.header("3. Recipe Suggestions")
        
        selected_titles = [s.title for s in st.session_state.suggestions]
        chosen_title = st.selectbox("Choose a recipe to see details:", selected_titles)
        
        if st.button("Get Final Recipe"):
            with st.spinner("Preparing detailed recipe..."):
                try:
                    final_recipe = recipe_pipeline.generate_final_recipe(
                        chosen_title,
                        st.session_state.ingredients,
                        user_preference, 
                        request_id
                    )
                    st.session_state.final_recipe = final_recipe
                except Exception as e:
                    st.error(f"Error generating final recipe: {e}")

    if "final_recipe" in st.session_state:
        st.divider()
        recipe = st.session_state.final_recipe
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
