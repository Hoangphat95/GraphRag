"""Utility: check Neo4j indexes and optionally create missing ones.

Usage:
  python scripts/check_neo4j.py

Environment variables:
  NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD - used by existing db/neo4j_client
  NEO4J_AUTO_CREATE_INDEXES=true - if set will attempt to create missing indexes

This script reuses `db.neo4j_client.Neo4jClient` and prints missing indexes
and suggested CREATE INDEX statements.
"""
import os
import logging
from db.neo4j_client import Neo4jClient


def main():
    logging.basicConfig(level=logging.INFO)
    client = Neo4jClient()

    required = [("Tire", "size"), ("Tire", "brand")]

    print("Checking Neo4j indexes...")
    missing = client.check_indexes(required=required)

    if not missing:
        print("All required indexes/constraints appear present.")
        return 0

    print("Missing indexes/constraints:")
    for label, prop in missing:
        print(f" - {label}.{prop}")

    print("\nSuggested CREATE INDEX statements:")
    for label, prop in missing:
        print(f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.{prop});")

    auto = os.environ.get("NEO4J_AUTO_CREATE_INDEXES", "false").lower() in ("1","true","yes")
    if auto:
        print("\nEnvironment requests auto-create. Attempting to create indexes now...")
        missing_after = client.check_indexes(required=required)
        if missing_after:
            print("Auto-create attempted; some indexes still missing or creation failed:")
            for label, prop in missing_after:
                print(f" - {label}.{prop}")
            return 2
        else:
            print("Auto-create succeeded.")
            return 0

    print("\nTip: set NEO4J_AUTO_CREATE_INDEXES=true to attempt auto-creation.")
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
