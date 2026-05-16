def build_cypher_prompt(query, schema):
    return f"""
You are an expert in Neo4j Cypher.

Graph schema:
{schema}

User question:
{query}

Rules:
- ONLY return Cypher query
- DO NOT explain
- Use correct property names from schema
- Always use MATCH (t:Tire) when querying tire info
- If filtering by size, use: WHERE t.size = "value"
- Limit result to 1 if asking single value

Cypher:
"""