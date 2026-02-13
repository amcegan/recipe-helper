import argparse
import asyncio
import sys
from recipe_helper.graph import create_recipe_graph
from recipe_helper.config import settings

async def run_graph_cli(inputs):
    """
    Run the recipe graph from the CLI.
    """
    print("Initializing Recipe Helper Graph...")
    graph = create_recipe_graph()
    
    config = {"configurable": {"thread_id": "cli-execution"}}
    
    print(f"Running graph with inputs: {inputs}")
    try:
        async for event in graph.astream(inputs, config):
            for k, v in event.items():
                print(f"Finished Node: {k}")
                # Print minimal output for clarity
                if "error" in v:
                    print(f"  Error: {v['error']}")
                elif "final_recipe" in v:
                    print(f"  Recipe Generated: {v['final_recipe'].title}")
    except Exception as e:
        print(f"Graph execution failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Run the Recipe Helper Graph CLI.")
    parser.add_argument("--city", help="Override city for weather context", default="Dublin")
    # For a real CLI, we might want ways to pass image paths or ingredients directly.
    # For now, this is a skeleton to prove the entry point works.
    
    args = parser.parse_args()
    
    # Example input - in a real CLI we'd probably require an image path or pre-extracted ingredients
    inputs = {
        "user_preference": "healthy",
        # CLI limitations: passing binary image data is hard without a file argument.
        # This is primarily a placeholder for future CLI expansion.
        "request_id": "cli-run-1"
    }
    
    try:
        asyncio.run(run_graph_cli(inputs))
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
