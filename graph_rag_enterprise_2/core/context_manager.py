import os
import sqlite3
import json
import time
try:
    import redis
except Exception:
    redis = None


class ContextManager:

    def __init__(self, backend="sqlite", db_path=None):
        # backend: 'sqlite' or 'memory'
        self.backend = backend
        if db_path:
            self.db_path = db_path
        else:
            base = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(base, "../.context.db")

        self.history = []

        if self.backend == "sqlite":
            try:
                self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self._init_db()
            except Exception:
                # fallback to memory
                self.backend = "memory"
                self._conn = None
        else:
            self._conn = None
        if self.backend == "redis":
            # attempt to create redis client from env or defaults
            try:
                if redis is None:
                    raise RuntimeError("redis package not installed")
                redis_url = os.environ.get("REDIS_URL")
                if redis_url:
                    self._redis = redis.from_url(redis_url)
                else:
                    host = os.environ.get("REDIS_HOST", "localhost")
                    port = int(os.environ.get("REDIS_PORT", 6379))
                    db = int(os.environ.get("REDIS_DB", 0))
                    self._redis = redis.Redis(host=host, port=port, db=db, socket_connect_timeout=2)
                # quick ping
                self._redis.ping()
            except Exception:
                # fallback to memory
                self.backend = "memory"
                self._redis = None
        else:
            self._redis = None

    def _init_db(self):
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL,
                query TEXT,
                mapped TEXT,
                plan TEXT,
                data TEXT
            )
            """
        )
        self._conn.commit()

    def add_context(self, query, mapped, plan, data):
        if self.backend == "sqlite" and self._conn:
            cur = self._conn.cursor()
            cur.execute(
                "INSERT INTO contexts (ts, query, mapped, plan, data) VALUES (?, ?, ?, ?, ?)",
                (time.time(), query, json.dumps(mapped, ensure_ascii=False), json.dumps(plan, ensure_ascii=False), json.dumps(data, ensure_ascii=False))
            )
            self._conn.commit()
        elif self.backend == "redis" and self._redis:
            try:
                payload = json.dumps({
                    "ts": time.time(),
                    "query": query,
                    "mapped": mapped,
                    "plan": plan,
                    "data": data,
                }, ensure_ascii=False)
                # push to list
                self._redis.rpush("graph_rag_contexts", payload)
                # cap list length to 1000
                try:
                    maxlen = int(os.environ.get("CONTEXT_REDIS_MAXLEN", 1000))
                    self._redis.ltrim("graph_rag_contexts", -maxlen, -1)
                except Exception:
                    pass
            except Exception:
                # degrade silently to memory
                self.history.append({
                    "query": query,
                    "mapped": mapped,
                    "plan": plan,
                    "data": data
                })
        else:
            self.history.append({
                "query": query,
                "mapped": mapped,
                "plan": plan,
                "data": data
            })

    def get_last(self):
        if self.backend == "sqlite" and self._conn:
            cur = self._conn.cursor()
            cur.execute("SELECT query, mapped, plan, data FROM contexts ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            if not row:
                return None
            q, mapped_s, plan_s, data_s = row
            return {
                "query": q,
                "mapped": json.loads(mapped_s),
                "plan": json.loads(plan_s) if plan_s else None,
                "data": json.loads(data_s) if data_s else None,
            }
        if self.backend == "redis" and self._redis:
            try:
                row = self._redis.lindex("graph_rag_contexts", -1)
                if not row:
                    return None
                obj = json.loads(row)
                return obj
            except Exception:
                return None
        else:
            return self.history[-1] if self.history else None

    def get_last_sizes(self, n=2):
        sizes = []
        if self.backend == "sqlite" and self._conn:
            cur = self._conn.cursor()
            cur.execute("SELECT mapped FROM contexts ORDER BY id DESC LIMIT ?", (n * 5,))
            rows = cur.fetchall()
            # iterate recent rows to collect sizes
            for (mapped_s,) in rows:
                try:
                    mapped = json.loads(mapped_s)
                except Exception:
                    continue
                for m in mapped:
                    if m.get("column") == "size":
                        value = m.get("value")
                        if value and value not in sizes:
                            sizes.append(value)
                if len(sizes) >= n:
                    break
            return sizes[:n]

        if self.backend == "redis" and self._redis:
            try:
                # fetch recent N*5 entries to be safe
                rows = self._redis.lrange("graph_rag_contexts", - (n * 5), -1)
                if not rows:
                    return []
                for raw in reversed(rows):
                    try:
                        mapped = json.loads(raw).get('mapped', [])
                    except Exception:
                        continue
                    for m in mapped:
                        if m.get("column") == "size":
                            value = m.get("value")
                            if value and value not in sizes:
                                sizes.append(value)
                    if len(sizes) >= n:
                        break
                return sizes[:n]
            except Exception:
                return []

        # memory fallback
        for entry in self.history:
            for m in entry.get("mapped", []):
                if m.get("column") == "size":
                    value = m.get("value")
                    if value and value not in sizes:
                        sizes.append(value)
        return sizes[-n:]

    def get_last_size(self):
        sizes = self.get_last_sizes(1)
        return sizes[0] if sizes else None

    def get_last_brand(self):
        last = self.get_last()
        if not last:
            return None

        brands = [m.get("value") for m in last.get("mapped", []) if m.get("column") == "brand"]
        return brands[-1] if brands else None