"""
Benchmark script to verify parallel execution using concurrent.futures.
This script runs several CPU-heavy tasks and measures the total elapsed time
to confirm they are executed in parallel.
"""
import asyncio
import time
from src.executor import run_cpu_bound

def cpu_heavy_task(name: str, duration: int) -> str:
    """
    Simulates a CPU-heavy task by sleeping (blocking).

    Args:
        name (str): Name of the task.
        duration (int): Duration in seconds to sleep.

    Returns:
        str: Completion message.
    """
    print(f"Starting task {name} for {duration}s...")
    time.sleep(duration)
    return f"Task {name} completed."

async def main():
    """Main entry point to run parallel tasks."""
    print("Starting concurrency verification...")
    start_time = time.perf_counter()
    
    # We run three tasks, each taking 2 seconds.
    # If parallel, total time should be ~2s. If serial, ~6s.
    tasks = [
        run_cpu_bound(cpu_heavy_task, "A", 2),
        run_cpu_bound(cpu_heavy_task, "B", 2),
        run_cpu_bound(cpu_heavy_task, "C", 2)
    ]
    
    results = await asyncio.gather(*tasks)
    
    elapsed = time.perf_counter() - start_time
    for r in results:
        print(r)
    
    print(f"\nTotal elapsed time: {elapsed:.2f}s")
    if elapsed < 3:
        print("SUCCESS: Parallel execution confirmed!")
    else:
        print("FAILURE: Execution appears to be serial.")

if __name__ == "__main__":
    asyncio.run(main())
