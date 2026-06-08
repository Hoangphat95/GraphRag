from typing import Optional
from . import audit


def generate_cypher_with_validation(llm, prompt: str, validator, retries: int = 1) -> Optional[str]:
    """Use an LLM to generate a Cypher query and validate it using the provided validator.

    Returns a valid cypher string or None if LLM failed to produce a valid cypher.
    """
    if not llm:
        return None

    cypher = llm.chat(prompt)
    if not cypher:
        return None

    cypher = cypher.replace("```cypher", "").replace("```", "").strip()
    # Audit LLM output (redacted)
    try:
        audit.log_generated(cypher, prompt=prompt)
    except Exception:
        pass

    valid, reason = validator.validate(cypher, params=None)
    if valid:
        return cypher

    # single retry with instruction to fix
    for _ in range(retries):
        re_prompt = (
            prompt
            + "\n\nFix the Cypher query so it follows the rules and uses the schema. Only return the Cypher query."
        )
        cypher2 = llm.chat(re_prompt)
        if not cypher2:
            continue
        cypher2 = cypher2.replace("```cypher", "").replace("```", "").strip()
        valid2, _ = validator.validate(cypher2, params=None)
        if valid2:
            return cypher2

    return None
# llm/tool_calling.py
def tool_cypher(query):
    return f"CALL CYPHER FOR: {query}"