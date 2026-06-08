def build_cypher_prompt(query, schema, detected_size=None):
    """Build a strict prompt for the LLM.

    If `detected_size` is provided, instruct the model to include
    `WHERE t.size = "{detected_size}"` in the Cypher.
    """

    size_note = ""
    if detected_size:
        size_note = f"If the user mentions size, ensure you include: WHERE t.size = \"{detected_size}\"\n"

    return f"""
You are an expert in Neo4j Cypher.

Graph schema:
{schema}

User question:
{query}

Rules (follow exactly):
- ONLY return the Cypher query and nothing else.
- DO NOT add explanation, notes, or commentary.
- Use only property and label names from the provided schema.
- Always use `MATCH (t:Tire)` when querying tire info.
- If the user mentions a tire size, include `WHERE t.size = "{detected_size}"` as shown above.
- Use these canonical aliases in RETURN: `size`, `brand`, `max_speed`, `max_load`, `pressure`, `diameter`, `rim`, `structure`, `pattern`, `price`.
- For single-value queries return `LIMIT 1` and return the value with the canonical alias.
- Do not use dangerous Cypher clauses: DELETE, CREATE, MERGE, SET, DROP, CALL.
- Output must be a single Cypher statement. Do not output multiple statements separated by `;`.

Cypher:
"""