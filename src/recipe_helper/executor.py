"""
Module for managing parallel execution using concurrent.futures.
Provides a thread-safe singleton ProcessPoolExecutor for handling CPU-bound tasks.
"""
import asyncio
import threading
from concurrent.futures import ProcessPoolExecutor
from typing import Callable, Any
from recipe_helper.logger import log_entry_exit

_executor = None
_executor_lock = threading.Lock()

def get_executor():
    """
    Returns a thread-safe singleton ProcessPoolExecutor instance.
    The executor is initialized with a fixed number of workers.

    Returns:
        ProcessPoolExecutor: The global process pool executor.
    """
    global _executor
    with _executor_lock:
        if _executor is None:
            # Initialize the executor with 4 workers as a reasonable default
            _executor = ProcessPoolExecutor(max_workers=4)
        return _executor

@log_entry_exit
async def run_cpu_bound(func: Callable, *args, **kwargs) -> Any:
    """
    Runs a CPU-bound function in a separate process to avoid blocking the event loop.
    Compatible with LangGraph (async) and Streamlit environments.

    Args:
        func (Callable): The function to execute.
        *args: Variable length argument list for the function.
        **kwargs: Arbitrary keyword arguments for the function.

    Returns:
        Any: The result of the function execution.
    """
    loop = asyncio.get_running_loop()
    executor = get_executor()
    
    # ProcessPoolExecutor.submit doesn't support kwargs directly for the function call.
    # We wrap it in a partial-like way if kwargs are provided.
    if kwargs:
        def wrapper():
            return func(*args, **kwargs)
        return await loop.run_in_executor(executor, wrapper)
    
    return await loop.run_in_executor(executor, func, *args)