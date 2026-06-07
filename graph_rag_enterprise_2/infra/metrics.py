import time
import logging

logger = logging.getLogger(__name__)


class Metrics:

    def __init__(self):
        self.logs = []

    def start_timer(self):
        return time.time()

    def end_timer(self, start_time):
        return round(time.time() - start_time, 3)

    def log(self, query, cypher, result, latency):

        record = {
            "query": query,
            "cypher": cypher if len(cypher) < 1000 else cypher[:1000] + "...",
            "result_count": len(result) if result else 0,
            "latency": latency
        }

        self.logs.append(record)

        # structured debug
        logger.debug("metrics.record %s", record)

    def dump_to_file(self, path: str):
        try:
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.logs, f, ensure_ascii=False, indent=2)
            logger.info("Metrics dumped to %s", path)
        except Exception:
            logger.exception("Failed to dump metrics to file")