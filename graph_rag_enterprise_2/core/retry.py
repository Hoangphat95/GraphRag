# core/retry.py
import time

def retry(func, retries=3):
    for i in range(retries):
        try:
            return func()
        except Exception:
            time.sleep(0.5)
    return None