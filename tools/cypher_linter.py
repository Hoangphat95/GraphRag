"""Simple static Cypher linter/checker.

Usage: `python -m tools.cypher_linter path/to/file.cypher` or import `lint_text`.
This is intentionally lightweight: it looks for common anti-patterns such as
- unconstrained `MATCH (n)` without a WHERE
- use of `DETACH DELETE` (dangerous)
- very large `LIMIT` or missing LIMIT in deletions
"""
import re
from typing import List


def lint_text(text: str) -> List[str]:
    issues = []
    s = text
    # look for MATCH ... RETURN without WHERE when pattern may be unconstrained
    for m in re.finditer(r"MATCH\s+\(([^)]+)\)", s, flags=re.IGNORECASE):
        snippet = m.group(0)
        # crude check: if no WHERE before next RETURN/DELETE and the variable is single-letter
        start = m.end()
        tail = s[start:start+200]
        if not re.search(r"WHERE", tail, flags=re.IGNORECASE):
            issues.append(f"Unconstrained MATCH may be expensive: '{snippet}'")

    if re.search(r"DETACH\s+DELETE", s, flags=re.IGNORECASE):
        issues.append("Use of DETACH DELETE found — verify you intend to remove relationships and nodes.")

    # suspicious cartesian product operator
    if re.search(r"\,\s*\(|\)\s*\,", s):
        issues.append("Possible cartesian product (comma-separated patterns) — consider using explicit relationships or WHERE filters.")

    # very large LIMIT or missing LIMIT on DELETE
    if re.search(r"DELETE\s+", s, flags=re.IGNORECASE) and not re.search(r"LIMIT\s+\d+", s, flags=re.IGNORECASE):
        issues.append("DELETE without LIMIT found — ensure this is intentional and safe.")

    return issues


if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        print("Usage: python -m tools.cypher_linter path/to/file.cypher")
        sys.exit(2)
    print(f"Linting {path}")
    txt = open(path, 'r', encoding='utf-8').read()
    for i in lint_text(txt):
        print("- ", i)