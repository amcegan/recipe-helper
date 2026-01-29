import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Callable, Any
import functools

# Global executor to reuse processes
# None initialization to allow lazy loading if needed, but we'll init it.
cpu_executor = ProcessPoolExecutor()

async def run_cpu_bound(func: Callable, *args, **kwargs) -> Any:
    """
    Runs a CPU-bound function in a separate process pool.
    Usage: result = await run_cpu_bound(my_cpu_heavy_func, arg1, kwarg=val)
    """
    loop = asyncio.get_running_loop()
    # functools.partial is used because loop.run_in_executor doesn't support kwargs
    pfunc = functools.partial(func, *args, **kwargs)
    return await loop.run_in_executor(cpu_executor, pfunc)
