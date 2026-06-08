import threading
from collections import defaultdict

_lock = threading.Lock()
_counters = defaultdict(int)


def increment(name: str, amount: int = 1):
    with _lock:
        _counters[name] += amount


def get_metrics():
    with _lock:
        return dict(_counters)


def reset_metrics():
    with _lock:
        _counters.clear()


def dump_to_file(path: str):
    import json
    with _lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_counters, f, ensure_ascii=False, indent=2)
