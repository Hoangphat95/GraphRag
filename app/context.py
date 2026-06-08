"""Context manager — stores conversation context in Redis (when available) or in-memory.

SQLite/local-DB support has been removed.  Only Redis or in-memory backends remain.
"""
import os
import json
import time

try:
    import redis
except Exception:
    redis = None


class ContextManager:
    """Stores conversation context for multi-turn resolution.

    Backend selection (in order of priority):
      1. Redis  – when ``REDIS_URL`` env var is set **and** ``redis`` package is installed.
      2. Memory – fallback (no persistence across restarts).
    """

    def __init__(self):
        self.backend = "memory"
        self._redis = None
        self._history = []  # in-memory fallback

        redis_url = os.environ.get("REDIS_URL")
        if redis and redis_url:
            try:
                self._redis = redis.from_url(redis_url)
                self._redis.ping()
                self.backend = "redis"
            except Exception:
                self._redis = None

    # ── write ────────────────────────────────────────────────────────────

    def add_context(self, query, mapped, plan, data):
        payload = {
            "ts": time.time(),
            "query": query,
            "mapped": mapped,
            "plan": plan,
            "data": data,
        }

        if self.backend == "redis" and self._redis:
            try:
                raw = json.dumps(payload, ensure_ascii=False)
                self._redis.rpush("graph_rag_contexts", raw)
                maxlen = int(os.environ.get("CONTEXT_REDIS_MAXLEN", 1000))
                self._redis.ltrim("graph_rag_contexts", -maxlen, -1)
                return
            except Exception:
                pass  # fall through to memory

        self._history.append(payload)

    # ── read helpers ─────────────────────────────────────────────────────

    def get_last(self):
        if self.backend == "redis" and self._redis:
            try:
                raw = self._redis.lindex("graph_rag_contexts", -1)
                if raw:
                    return json.loads(raw)
            except Exception:
                pass
            return None

        return self._history[-1] if self._history else None

    def get_last_sizes(self, n=2):
        sizes = []

        if self.backend == "redis" and self._redis:
            try:
                rows = self._redis.lrange("graph_rag_contexts", -(n * 5), -1)
                if not rows:
                    return []
                for raw in reversed(rows):
                    try:
                        mapped = json.loads(raw).get("mapped", [])
                    except Exception:
                        continue
                    for m in mapped:
                        if m.get("column") == "size":
                            val = m.get("value")
                            if val and val not in sizes:
                                sizes.append(val)
                    if len(sizes) >= n:
                        break
                return sizes[:n]
            except Exception:
                return []

        for entry in self._history:
            for m in entry.get("mapped", []):
                if m.get("column") == "size":
                    val = m.get("value")
                    if val and val not in sizes:
                        sizes.append(val)
        return sizes[-n:] if sizes else []

    def get_last_size(self):
        sizes = self.get_last_sizes(1)
        return sizes[0] if sizes else None

    def get_last_brand(self):
        last = self.get_last()
        if not last:
            return None
        brands = [m.get("value") for m in last.get("mapped", []) if m.get("column") == "brand"]
        return brands[0] if brands else None
