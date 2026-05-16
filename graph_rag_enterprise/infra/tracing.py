# infra/tracing.py
import time

def trace(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        print(f"[TRACE] {func.__name__}: {time.time()-start:.3f}s")
        return res
    return wrapper