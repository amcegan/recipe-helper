import asyncio
import time
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from src.executor import run_cpu_bound

def cpu_heavy_task(name, duration):
    print(f"Starting task {name} for {duration}s...")
    time.sleep(duration)
    print(f"Finished task {name}.")
    return f"Result of {name}"

async def main():
    print("Starting Dask verification...")
    # Run multiple tasks in parallel
    tasks = [
        run_cpu_bound(cpu_heavy_task, "Task A", 2),
        run_cpu_bound(cpu_heavy_task, "Task B", 2),
        run_cpu_bound(cpu_heavy_task, "Task C", 2),
    ]
    
    start_time = time.perf_counter()
    results = await asyncio.gather(*tasks)
    end_time = time.perf_counter()
    
    print(f"Results: {results}")
    duration = end_time - start_time
    print(f"Total time taken: {duration:.2f} seconds")
    
    if duration < 5: # If they ran in parallel, it should be ~2-3s
        print("Verification SUCCESS: Tasks ran in parallel.")
    else:
        print("Verification FAILURE: Tasks seem to have run sequentially or startup took too long.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"An error occurred: {e}")
