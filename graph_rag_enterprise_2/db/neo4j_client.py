import time
import logging
import os
from neo4j import GraphDatabase
from config.settings import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from validation.cypher_validator import CypherValidator
from utils.normalizer import normalize_data
from infra import metrics_prometheus as metrics
try:
    from opentelemetry import trace as ot_trace
except Exception:
    ot_trace = None

logger = logging.getLogger(__name__)


class Neo4jClient:

    def __init__(self, max_retries: int = None, query_timeout: int = None):
        self.max_retries = int(os.environ.get("NEO4J_MAX_RETRIES", 2)) if max_retries is None else max_retries
        self.query_timeout = int(os.environ.get("NEO4J_QUERY_TIMEOUT", 30)) if query_timeout is None else query_timeout

        # create driver; rely on URI scheme (neo4j+s) for secure transport when configured
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            max_connection_lifetime=int(os.environ.get("NEO4J_MAX_CONN_LIFETIME", 3600))
        )

    def close(self):
        try:
            self.driver.close()
        except Exception:
            logger.exception("Error closing Neo4j driver")

    def query(self, cypher: str, params: dict = None, timeout: int = None, validate: bool = False):
        """Execute a Cypher query with optional parameters, retries and basic validation.

        Returns list of record dictionaries.
        """
        if timeout is None:
            timeout = self.query_timeout

        # basic validation to avoid dangerous statements
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

        # execute with simple retry/backoff
        last_exc = None
        for attempt in range(self.max_retries + 1):
            start = time.time()
            try:
                with self.driver.session() as session:
                    if ot_trace is not None:
                        tracer = ot_trace.get_tracer(__name__)
                        import hashlib
                        stmt_hash = hashlib.sha256(cypher.encode('utf-8')).hexdigest()[:12]
                        attr = {
                            "db.system": "neo4j",
                            "db.statement.hash": stmt_hash,
                            "db.statement.length": len(cypher),
                            "db.params.count": len(params) if params else 0,
                            "attempt": attempt,
                        }
                        with tracer.start_as_current_span("neo4j.query", attributes=attr) as span:
                            result = session.run(cypher, params or {}, timeout=timeout)
                            span.set_attribute('neo4j.rows_expected', 0)
                    else:
                        result = session.run(cypher, params or {}, timeout=timeout)
                    data = [r.data() for r in result]

                    # normalize records to canonical keys for all consumers
                    data = normalize_data(data)

                    latency = round(time.time() - start, 3)
                    logger.info("Cypher executed rows=%d latency=%.3fs", len(data), latency)
                    try:
                        if ot_trace is not None:
                            try:
                                tracer = ot_trace.get_tracer(__name__)
                                span = tracer.get_current_span()
                                if span is not None:
                                    span.set_attribute('neo4j.rows', len(data))
                                    span.set_attribute('neo4j.success', True)
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        if metrics.query_latency is not None:
                            metrics.query_latency.observe(latency)
                        if metrics.neo4j_query_counter is not None:
                            metrics.neo4j_query_counter.labels(success="true").inc()
                        if metrics.neo4j_rows is not None:
                            metrics.neo4j_rows.observe(len(data))
                    except Exception:
                        pass
                    return data

            except Exception as e:
                last_exc = e
                logger.exception("Neo4j query attempt %d failed", attempt + 1)
                if ot_trace is not None:
                    try:
                        tracer = ot_trace.get_tracer(__name__)
                        span = tracer.get_current_span()
                        if span is not None:
                            span.record_exception(e)
                            span.set_attribute('neo4j.success', False)
                    except Exception:
                        pass
                try:
                    if metrics.neo4j_query_counter is not None:
                        metrics.neo4j_query_counter.labels(success="false").inc()
                    if metrics.neo4j_query_failures is not None:
                        metrics.neo4j_query_failures.inc()
                except Exception:
                    pass
                if attempt < self.max_retries:
                    backoff = 0.5 * (2 ** attempt)
                    time.sleep(backoff)
                    continue
                else:
                    logger.error("All Neo4j query attempts failed")
                    raise

    def check_indexes(self, required: list = None):
        """Check for presence of indexes/constraints for required (label, property) pairs.

        Returns list of missing (label, property) pairs.
        """
        if required is None:
            required = [("Tire", "size"), ("Tire", "brand")]

        try:
            with self.driver.session() as session:
                # db.indexes() works across Neo4j versions; fallback to procedure call
                if ot_trace is not None:
                    tracer = ot_trace.get_tracer(__name__)
                    with tracer.start_as_current_span('neo4j.check_indexes', attributes={'db.system': 'neo4j'}):
                        result = session.run("CALL db.indexes()")
                else:
                    result = session.run("CALL db.indexes()")
                rows = [dict(r) for r in result]

                text = "\n".join([str(r) for r in rows])

                missing = []
                for label, prop in required:
                    if prop not in text:
                        missing.append((label, prop))

                # optionally auto-create missing indexes if environment requests
                auto_create = os.environ.get("NEO4J_AUTO_CREATE_INDEXES", "false").lower() in ("1", "true", "yes")
                if missing and auto_create:
                    for label, prop in missing:
                        try:
                            # use modern CREATE INDEX syntax with IF NOT EXISTS when supported
                            stmt = f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.{prop})"
                            session.run(stmt)
                        except Exception:
                            logger.exception("Failed to create index for %s.%s", label, prop)

                return missing
        except Exception:
            logger.exception("Failed to fetch Neo4j indexes")
            return required
