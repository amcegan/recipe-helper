import asyncio
import threading
from typing import Callable, Any
from distributed import Client

_dask_client = None
_client_lock = threading.Lock()

def get_client():
    """
    Returns a thread-safe, synchronous Dask Client.
    Synchronous clients are more robust in Streamlit's ephemeral event loop environment
    because they manage their own internal lifecycle independent of the calling thread's loop.
    """
    global _dask_client
    with _client_lock:
        if _dask_client is None or getattr(_dask_client, "status", None) != "running":
            # Using synchronous Client (asynchronous=False)
            # This creates a persistent cluster that survives asyncio.run() calls.
            _dask_client = Client(n_workers=4, threads_per_worker=1, asynchronous=False)
        return _dask_client

async def run_cpu_bound(func: Callable, *args, **kwargs) -> Any:
    """
    Runs a CPU-bound function using Dask.
    Compatible with LangGraph (async) and Streamlit (multiple asyncio.run calls).
    """
    # Get the sync client in a thread-safe way
    client = await asyncio.to_thread(get_client)
    
    # Submit the task to Dask (non-blocking, returns a sync Future)
    future = client.submit(func, *args, **kwargs)
    
    # Await the result in a separate thread to avoid blocking the current event loop
    return await asyncio.to_thread(future.result)