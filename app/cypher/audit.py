import os
import re
import time

LOG_PATH = os.environ.get('LLM_CYPHER_AUDIT_LOG', os.path.join(os.path.dirname(__file__), '../logs/llm_cypher.log'))


def _redact_literals(cypher: str) -> str:
    # replace content inside single or double quotes with <REDACTED>
    cy = re.sub(r"'[^']*'", "'<REDACTED>'", cypher)
    cy = re.sub(r'"[^"]*"', '"<REDACTED>"', cy)
    return cy


def log_generated(cypher: str, prompt: str = None):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            ts = time.strftime('%Y-%m-%dT%H:%M:%S')
            redacted = _redact_literals(cypher)
            f.write(f"{ts} | CY: {redacted}\n")
            if prompt:
                redacted_prompt = prompt[:1000].replace('\n', ' ').replace('\r', ' ')
                f.write(f"{ts} | PROMPT: {redacted_prompt}\n")
    except Exception:
        pass
