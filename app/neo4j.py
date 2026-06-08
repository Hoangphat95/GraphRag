"""Neo4j Service — standalone database client.

Reads config from ``app.config`` (which reads from env / Vault / K8s secrets).
Supports both ``NEO4J_USER`` and ``NEO4J_USERNAME`` env vars (Aura-compatible).

Features:
  - Connection pooling via ``neo4j.GraphDatabase.driver``
  - Retry with exponential backoff
  - Prometheus metrics (latency, row count, success/failure counters)
  - OpenTelemetry tracing (span per query)
  - Cypher validation (optional)
  - Transaction helper (``run_in_tx``)
  - Schema utilities: ``check_indexes``, ``list_labels``, ``list_relationship_types``
  - Health check: ``ping()``
  - Context-manager support (async ``__aenter__`` / ``__aexit__``)
"""
from __future__ import annotations

import time
import logging
import os
import hashlib
from typing import Any, Optional

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, SessionExpired, TransientError

from app.config import NEO4J_URI, NEO4J_PASSWORD

# ── Resolve Neo4j username (support both env-var names) ──────────────────────
_NEO4J_USER = os.environ.get("NEO4J_USER") or os.environ.get("NEO4J_USERNAME") or "neo4j"

from app.cypher.validator import CypherValidator  # noqa: E402
from app.normalizer import normalize_data  # noqa: E402
from app import metrics  # noqa: E402, F401 – ensure metrics module is importable

try:
    from opentelemetry import trace as ot_trace
except Exception:
    ot_trace = None

logger = logging.getLogger(__name__)

# ── Errors we consider retryable ─────────────────────────────────────────────
_RETRYABLE = (ServiceUnavailable, SessionExpired, TransientError, ConnectionError, TimeoutError)


# ═══════════════════════════════════════════════════════════════════════════════
#  Neo4jClient
# ═══════════════════════════════════════════════════════════════════════════════
class Neo4jClient:
    """Standalone Neo4j service client.

    Usage::

        db = Neo4jClient()
        rows = db.query("MATCH (t:Tire) RETURN t LIMIT 5")
        db.close()

    Or as an async context manager::

        async with Neo4jClient() as db:
            rows = await db.run_in_tx("MATCH (t:Tire) RETURN t LIMIT 5")
    """

    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
        max_retries: int | None = None,
        query_timeout: int | None = None,
        max_connection_lifetime: int | None = None,
        database: str | None = None,
    ):
        self._uri = uri or NEO4J_URI
        self._user = user or _NEO4J_USER
        self._password = password or NEO4J_PASSWORD
        self._database = database or os.environ.get("NEO4J_DATABASE") or "neo4j"

        self.max_retries = max_retries if max_retries is not None else int(os.environ.get("NEO4J_MAX_RETRIES", "2"))
        self.query_timeout = query_timeout if query_timeout is not None else int(os.environ.get("NEO4J_QUERY_TIMEOUT", "30"))
        self.max_connection_lifetime = max_connection_lifetime if max_connection_lifetime is not None else int(os.environ.get("NEO4J_MAX_CONN_LIFETIME", "3600"))

        self._driver = None
        self._open = False

    # ── Properties ─────────────────────────────────────────────────────────

    @property
    def driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password),
                max_connection_lifetime=self.max_connection_lifetime,
            )
            self._open = True
        return self._driver

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def close(self):
        if self._driver is not None:
            try:
                self._driver.close()
            except Exception:
                logger.exception("Error closing Neo4j driver")
            finally:
                self._driver = None
                self._open = False

    async def __aenter__(self) -> "Neo4jClient":
        _ = self.driver  # lazy init
        return self

    async def __aexit__(self, *exc_info) -> None:
        self.close()

    # ── Core query ─────────────────────────────────────────────────────────

    def query(
        self,
        cypher: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: int | None = None,
        validate: bool = False,
        database: str | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query with retry, metrics & optional tracing.

        Parameters
        ----------
        cypher : str
            Cypher statement to execute.
        params : dict or None
            Named parameters for the Cypher statement.
        timeout : int or None
            Query timeout in seconds (default: ``self.query_timeout``).
        validate : bool
            If ``True``, run ``CypherValidator`` before executing.
        database : str or None
            Target database (default: ``self._database``).

        Returns
        -------
        list[dict]
            List of record dictionaries with canonical keys (via ``normalize_data``).
        """
        if timeout is None:
            timeout = self.query_timeout
        db_name = database or self._database

        # ── optional validation ────────────────────────────────────────────
        if validate:
            try:
                validator = CypherValidator()
                valid, reason = validator.validate(cypher, params=params)
                if not valid:
                    logger.warning("Refusing to execute invalid Cypher: %s", reason)
                    raise ValueError(f"Invalid Cypher: {reason}")
            except Exception:
                logger.exception("Validator error; refusing to execute Cypher")
                raise

        # ── execute with retry ─────────────────────────────────────────────
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            start = time.time()
            try:
                with self.driver.session(database=db_name) as session:
                    if ot_trace is not None:
                        tracer = ot_trace.get_tracer(__name__)
                        stmt_hash = hashlib.sha256(cypher.encode("utf-8")).hexdigest()[:12]
                        attrs = {
                            "db.system": "neo4j",
                            "db.statement.hash": stmt_hash,
                            "db.statement.length": len(cypher),
                            "db.params.count": len(params) if params else 0,
                            "attempt": attempt,
                        }
                        with tracer.start_as_current_span("neo4j.query", attributes=attrs):
                            result = session.run(cypher, params or {}, timeout=timeout)
                    else:
                        result = session.run(cypher, params or {}, timeout=timeout)

                    data = [r.data() for r in result]

                data = normalize_data(data)
                latency = round(time.time() - start, 3)
                logger.info("[NEO4J] rows=%d latency=%.3fs db=%s", len(data), latency, db_name)

                self._record_metrics(latency, len(data), success=True)
                return data

            except _RETRYABLE as e:
                last_exc = e
                logger.warning("[NEO4J] retryable error (attempt %d/%d): %s", attempt + 1, self.max_retries + 1, e)
                self._record_metrics(None, 0, success=False)
                if attempt < self.max_retries:
                    time.sleep(0.5 * (2**attempt))
                    continue
                logger.error("[NEO4J] all %d attempts failed", self.max_retries + 1)
                raise

            except Exception as e:
                last_exc = e
                logger.exception("[NEO4J] non-retryable error (attempt %d)", attempt + 1)
                self._record_metrics(None, 0, success=False)
                raise

        # unreachable, but mypy safety
        raise RuntimeError("Neo4j query failed after retries") from last_exc

    # ── Transaction helper ─────────────────────────────────────────────────

    def run_in_tx(
        self,
        cypher: str,
        params: dict[str, Any] | None = None,
        *,
        database: str | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a query inside a managed transaction.

        Useful when you need transactional guarantees (rollback on failure).
        """
        db_name = database or self._database
        with self.driver.session(database=db_name) as session:
            result = session.execute_read(lambda tx: list(tx.run(cypher, params or {})))
        return [r.data() for r in result]

    # ── Schema utilities ───────────────────────────────────────────────────

    def list_labels(self) -> list[str]:
        """Return all node labels in the graph."""
        try:
            rows = self.query("CALL db.labels()")
            return sorted(r.get("label", "") for r in rows if r.get("label"))
        except Exception:
            logger.exception("Failed to list labels")
            return []

    def list_relationship_types(self) -> list[str]:
        """Return all relationship types in the graph."""
        try:
            rows = self.query("CALL db.relationshipTypes()")
            return sorted(r.get("relationshipType", "") for r in rows if r.get("relationshipType"))
        except Exception:
            logger.exception("Failed to list relationship types")
            return []

    def list_properties(self, label: str) -> list[str]:
        """Return all property keys for a given node label."""
        try:
            rows = self.query(
                f"MATCH (n:`{label}`) UNWIND keys(n) AS prop RETURN DISTINCT prop ORDER BY prop"
            )
            return [r["prop"] for r in rows]
        except Exception:
            logger.exception("Failed to list properties for label %s", label)
            return []

    def check_indexes(self, required: list[tuple[str, str]] | None = None) -> list[tuple[str, str]]:
        """Check (and optionally auto-create) indexes.

        Parameters
        ----------
        required : list of (label, property) tuples
            Indexes to verify (default: ``[("Tire", "size"), ("Tire", "brand")]``).

        Returns
        -------
        list[tuple[str, str]]
            List of (label, property) tuples that are *missing*.
        """
        if required is None:
            required = [("Tire", "size"), ("Tire", "brand")]

        try:
            with self.driver.session() as session:
                span_ctx = None
                if ot_trace is not None:
                    tracer = ot_trace.get_tracer(__name__)
                    span_ctx = tracer.start_as_current_span(
                        "neo4j.check_indexes", attributes={"db.system": "neo4j"}
                    )
                    span_ctx.__enter__()

                try:
                    result = session.run("CALL db.indexes()")
                finally:
                    if span_ctx is not None:
                        span_ctx.__exit__(None, None, None)

                rows = [dict(r) for r in result]
                text = "\n".join(str(r) for r in rows)

                missing = [(lbl, prop) for lbl, prop in required if prop not in text]

                auto_create = os.environ.get("NEO4J_AUTO_CREATE_INDEXES", "false").lower() in (
                    "1",
                    "true",
                    "yes",
                )
                if missing and auto_create:
                    for label, prop in missing:
                        try:
                            stmt = f"CREATE INDEX IF NOT EXISTS FOR (n:`{label}`) ON (n.`{prop}`)"
                            session.run(stmt)
                            logger.info("Created index %s.%s", label, prop)
                        except Exception:
                            logger.exception("Failed to create index for %s.%s", label, prop)

                return missing
        except Exception:
            logger.exception("Failed to fetch Neo4j indexes")
            return required

    # ── Health ─────────────────────────────────────────────────────────────

    def ping(self) -> bool:
        """Check connectivity by running a no-op query."""
        try:
            self.query("RETURN 1 AS ok", timeout=5)
            return True
        except Exception:
            logger.warning("[NEO4J] ping failed")
            return False

    def info(self) -> dict[str, Any]:
        """Return server info dict (version, labels, rel types, indexes)."""
        try:
            version = self.query("CALL dbms.components() YIELD versions RETURN versions")[0]["versions"][0]
        except Exception:
            version = "unknown"
        return {
            "uri": self._uri,
            "database": self._database,
            "version": version,
            "labels": self.list_labels(),
            "relationship_types": self.list_relationship_types(),
        }

    # ── Internals ──────────────────────────────────────────────────────────

    def _record_metrics(self, latency: float | None, rows: int, *, success: bool):
        try:
            if success:
                if latency is not None and metrics.query_latency is not None:
                    metrics.query_latency.observe(latency)
                if metrics.neo4j_query_counter is not None:
                    metrics.neo4j_query_counter.labels(success="true").inc()
                if metrics.neo4j_rows is not None:
                    metrics.neo4j_rows.observe(rows)
            else:
                if metrics.neo4j_query_counter is not None:
                    metrics.neo4j_query_counter.labels(success="false").inc()
                if metrics.neo4j_query_failures is not None:
                    metrics.neo4j_query_failures.inc()
        except Exception:
            pass
