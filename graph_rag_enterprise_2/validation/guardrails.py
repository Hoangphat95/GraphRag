# validation/guardrails.py
def check_dangerous_query(cypher):
    banned = ["DELETE", "DROP", "REMOVE"]
    return not any(b in cypher.upper() for b in banned)