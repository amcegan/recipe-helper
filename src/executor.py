import asyncio
from typing import Callable, Any
from distributed import Client

_dask_client = None
_client_lock = asyncio.Lock()

async def get_client():
    global _dask_client
    async with _client_lock:
        if _dask_client is None:
            # Initialize async client
            _dask_client = await Client(n_workreaers=4, threads_per_worker=1, asynchronous=True)
        return _dask_client

async def run_cpu_bound(func: Callable, *args, **kwargs) -> Any:
    """
    Runs a CPU-bound function using Dask.
    Usage: result = await run_cpu_bound(my_cpu_heavy_func, arg1, kwarg=val)
    """
    client = await get_client()
    # Submit the task to Dask
    future = client.submit(func, *args, **kwargs)
    # Await the result
    return await future