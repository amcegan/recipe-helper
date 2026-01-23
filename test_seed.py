import os
from src.recipes import RecipePipeline
from src.schemas import Ingredient
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def test_deterministic_suggestions():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        return

    pipeline = RecipePipeline(api_key)
    ingredients = [
        Ingredient(name="chicken breast", confidence=1.0),
        Ingredient(name="broccoli", confidence=1.0),
        Ingredient(name="soy sauce", confidence=1.0)
    ]
    request_id = "test-seed-123"
    seed = 42

    print("--- Running first generation with seed 42 ---")
    res1 = pipeline.suggest_recipes(ingredients, "healthy dinner", request_id, seed=seed)
    titles1 = [s.title for s in res1.suggestions]
    print(f"Result 1: {titles1}")

    print("\n--- Running second generation with seed 42 ---")
    res2 = pipeline.suggest_recipes(ingredients, "healthy dinner", request_id, seed=seed)
    titles2 = [s.title for s in res2.suggestions]
    print(f"Result 2: {titles2}")

    if titles1 == titles2:
        print("\nSUCCESS: Both results are identical!")
    else:
        print("\nFAILURE: Results differ despite same seed.")

if __name__ == "__main__":
    test_deterministic_suggestions()
