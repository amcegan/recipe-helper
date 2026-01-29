import streamlit as st
import uuid
from PIL import Image
from src.vision import VisionPipeline
from src.recipes import RecipePipeline
from src.logger import get_request_logger
import os
from src.exceptions import RateLimitError
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
    uploaded_files = st.file_uploader("Choose images...", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if uploaded_files:
        cols = st.columns(len(uploaded_files))
        for i, uploaded_file in enumerate(uploaded_files):
            with Image.open(uploaded_file) as image:
                cols[i].image(image, caption=f"Image {i+1}", use_container_width=True)

        if st.button("Detect Ingredients"):
            with st.spinner("Analyzing all images..."):
                try:
                    all_detected_ingredients = []
                    # Keep track of unique ingredient names to avoid duplicates across photos
                    seen_names = set()
                    
                    for uploaded_file in uploaded_files:
                        with Image.open(uploaded_file) as image:
                            ingredients = vision_pipeline.extract_ingredients(image, request_id)
                            for ing in ingredients.ingredients:
                                if ing.name.lower() not in seen_names:
                                    all_detected_ingredients.append(ing)
                                    seen_names.add(ing.name.lower())
                                else:
                                    # Update confidence if we see it again and it's higher? 
                                    # Or just skip. For now, let's just keep the first occurrence or highest confidence.
                                    for existing in all_detected_ingredients:
                                        if existing.name.lower() == ing.name.lower():
                                            existing.confidence = max(existing.confidence, ing.confidence)

                    st.session_state.ingredients = all_detected_ingredients
                    st.success(f"Detected {len(all_detected_ingredients)} unique ingredients across {len(uploaded_files)} images!")
                except RateLimitError as e:
                    st.warning("⚠️ API Rate limit reached. Please wait a moment before trying again.")
                    st.info(f"Details: {e}")
                except Exception as e:
                    st.error(f"Error extracting ingredients: {e}")

    if "ingredients" in st.session_state:
        st.divider()
        st.header("2. Detected Ingredients")
        
        # Display existing ingredients
        for ing in st.session_state.ingredients:
            confidence_color = "green" if ing.confidence > 0.8 else "orange" if ing.confidence > 0.5 else "red"
            st.markdown(f"- **{ing.name}** (Confidence: :{confidence_color}[{ing.confidence:.2f}])")
            if ing.notes:
                st.caption(f"Note: {ing.notes}")

        # Manual entry
        st.subheader("Add Extra Ingredient")
        col1, col2 = st.columns([3, 1])
        with col1:
            new_ing_name = st.text_input("Ingredient name", key="new_ing_name", label_visibility="collapsed", placeholder="Enter ingredient name...")
        with col2:
            if st.button("Add", use_container_width=True):
                if new_ing_name.strip():
                    from src.schemas import Ingredient
                    new_ing = Ingredient(name=new_ing_name.strip(), confidence=1.0, notes="Manually added")
                    st.session_state.ingredients.append(new_ing)
                    st.rerun()

        st.divider()

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
                except RateLimitError as e:
                    st.warning("⚠️ API Rate limit reached. Please wait a moment before trying again.")
                    st.info(f"Details: {e}")
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
                except RateLimitError as e:
                    st.warning("⚠️ API Rate limit reached. Please wait a moment before trying again.")
                    st.info(f"Details: {e}")
                except Exception as e:
                    st.error(f"Error generating final recipe: {e}")

    if "final_recipe" in st.session_state:
        st.divider()
        recipe = st.session_state.final_recipe
        st.header(f"📖 Final Recipe: {recipe.title}")
        
        st.subheader("Ingredients")
        for item in recipe.ingredients:
            st.write(f"- {item}")

        st.subheader("Instructions")
        for i, step in enumerate(recipe.steps, 1):
            st.write(f"{i}. {step}")
        
        if recipe.notes:
            st.subheader("Chef's Notes")
            st.write(recipe.notes)
    
    logger.debug("EXITING: render_ui")
