import os
import json
import logging
import re
from app.llm_client import LLMClient
from .prompt_cypher import build_cypher_prompt
from app.cypher.validator import CypherValidator
from .tool_calling import generate_cypher_with_validation
from .limits import SINGLE_LIMIT, MULTI_LIMIT
from . import metrics

logger = logging.getLogger(__name__)


class CypherGenerator:
    def __init__(self):
        # lazy init LLM client to avoid heavy work on import
        self.llm = None
        self.model_name = "models/gemini-3.1-flash-lite-preview"

        # ensure basic logging configured if app didn't configure logging
        if not logging.getLogger().handlers:
            logging.basicConfig(level=logging.INFO)

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(BASE_DIR, "graph_schema.json")

        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

        # validator instance
        self.validator = CypherValidator()

    def generate(self, query: str):
        # detect size early and pass to the prompt to force WHERE usage
        detected_size = self._extract_size_from_query(query)
        prompt = build_cypher_prompt(query, self.schema, detected_size)

        logger.debug("===== CYPHER PROMPT =====\n%s", prompt)

        # ensure llm client exists (lazy init)
        if not self.llm:
            try:
                self.llm = LLMClient(model_name=self.model_name)
            except Exception:
                logger.exception("Failed to initialize LLMClient")
                self.llm = None

        cypher = None
        if self.llm:
            cypher = self.llm.chat(prompt)

        logger.debug("===== RAW LLM CYPHER =====\n%s", cypher)

        if not cypher:
            logger.warning("LLM returned empty response; will fallback")
            try:
                metrics.increment("llm_empty")
            except Exception:
                logger.exception("Failed to increment metrics llm_empty")

        # centralize LLM call + validation
        cypher_valid = generate_cypher_with_validation(self.llm, prompt, self.validator, retries=1)
        if cypher_valid:
            try:
                metrics.increment("llm_valid")
            except Exception:
                logger.exception("Failed to increment metrics llm_valid")
            return cypher_valid

        logger.warning("LLM failed to produce a valid Cypher. Using deterministic fallback.")
        try:
            metrics.increment("fallback_used")
        except Exception:
            logger.exception("Failed to increment metrics fallback_used")

        # deterministic fallback: try to extract a size and build a safe query
        fallback = self._fallback_query(query)
        logger.info("===== FALLBACK CYPHER =====\n%s", fallback)
        return fallback

    def _extract_size_from_query(self, query: str):
        """Try to extract a tire size token from the user's query.

        Matches common forms like 205/55R16, 205/55, 205-55-16, or simple numeric sizes.
        Returns the first plausible token or None.
        """
        if not query:
            return None

        q = query.replace('\n', ' ')

        # common patterns
        patterns = [
            r"\b\d{3}/\d{2}R\d{2}\b",
            r"\b\d{3}/\d{2}R?\d{2}\b",
            r"\b\d{2,3}/\d{2,3}\b",
            r"\b\d{2,3}-\d{2,3}-?\d{0,2}\b",
            r"\bsize\s*[:=]?\s*(\d[\d/\w\-]+)\b",
        ]

        for p in patterns:
            m = re.search(p, q, flags=re.IGNORECASE)
            if m:
                # if capturing group present use it
                token = m.group(0)
                token = token.strip()
                # clean token
                token = token.replace('"', '').replace("'", '')
                return token

        return None

    def _fallback_query(self, query: str):
        size = self._extract_size_from_query(query)

        if size:
            safe_size = size.replace('"', '').replace("'", "")
            return f'''\
            MATCH (t:Tire)
            WHERE t.size = "{safe_size}"
            RETURN t.size AS size, t.brand AS brand, t.toc_do_toi_da AS max_speed
            LIMIT {SINGLE_LIMIT}
            '''

        # generic safe fallback
        return f'''\
        MATCH (t:Tire)
        RETURN DISTINCT t.size AS size
        LIMIT {MULTI_LIMIT}
        '''