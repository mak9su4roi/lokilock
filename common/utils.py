from functools import wraps
import time


def async_timeit(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter_ns()
        result = await func(*args, **kwargs)
        return result, (time.perf_counter_ns() - start_time) / 10**9

    return wrapper
