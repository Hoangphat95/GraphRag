# llm/tool_calling.py
def tool_cypher(query):
    return f"CALL CYPHER FOR: {query}"