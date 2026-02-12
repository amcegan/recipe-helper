"""
Verification script for Dask parallel execution.

This script runs a set of CPU-bound tasks in parallel using the Dask executor
to verify that the parallel processing infrastructure is correctly configured
and performing as expected.
"""

import asyncio
import time
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from src.executor import run_cpu_bound
from src.logger import setup_logger, get_request_logger, log_entry_exit

# Initialize the centralized logger
setup_logger()

def cpu_heavy_task(name: str, duration: int) -> str:
    """
    Simulates a CPU-heavy task by sleeping for a specified duration.

    Args:
        name: The name of the task for logging purposes.
        duration: The number of seconds to sleep.

    Returns:
        A result string indicating completion.
    """
    logger = get_request_logger()
    logger.info(f"Starting task {name}", task_name=name, duration=duration)
    time.sleep(duration)
    logger.info(f"Finished task {name}", task_name=name)
    return f"Result of {name}"

@log_entry_exit
async def main() -> None:
    """
    Orchestrates the verification of parallel task execution.

    Runs multiple CPU-bound tasks in parallel and measures the total elapsed time.
    If the total time is significantly less than the sum of task durations,
    parallelization is considered successful.
    """
    logger = get_request_logger()
    logger.info("Starting Dask verification")
    
    # Run multiple tasks in parallel
    tasks = [
        run_cpu_bound(cpu_heavy_task, "Task A", 2),
        run_cpu_bound(cpu_heavy_task, "Task B", 2),
        run_cpu_bound(cpu_heavy_task, "Task C", 2),
    ]
    
    start_time = time.perf_counter()
    results = await asyncio.gather(*tasks)
    end_time = time.perf_counter()
    
    duration = end_time - start_time
    logger.info("Dask verification completed", results=results, total_duration=round(duration, 2))
    
    if duration < 5: # If they ran in parallel, it should be ~2-3s
        logger.info("Verification SUCCESS: Tasks ran in parallel.")
    else:
        logger.error("Verification FAILURE: Tasks seem to have run sequentially or startup took too long.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger = get_request_logger()
        logger.exception("An unexpected error occurred during verification", error=str(e))
