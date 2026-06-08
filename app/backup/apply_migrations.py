import os
import datetime
from app.neo4j import Neo4jClient

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'migrations')


def applied_migrations(client: Neo4jClient):
    """Return set of applied migration names recorded in the DB."""
    try:
        rows = client.query("MATCH (m:Migration) RETURN m.name AS name", validate=False)
        return set(r.get('name') for r in rows)
    except Exception:
        # If the Migration label doesn't exist or DB unreachable, return empty set
        return set()


def record_migration(client: Neo4jClient, name: str):
    ts = datetime.datetime.utcnow().isoformat()
    stmt = (
        "CREATE (m:Migration {name: $name, applied_at: datetime($applied_at)})"
    )
    client.query(stmt, params={'name': name, 'applied_at': ts}, validate=False)


def apply_all():
    client = Neo4jClient()
    files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.cypher')])
    applied = applied_migrations(client)

    for fn in files:
        if fn in applied:
            print('Skipping already-applied', fn)
            continue
        path = os.path.join(MIGRATIONS_DIR, fn)
        with open(path, 'r', encoding='utf-8') as fh:
            stmt = fh.read()
            print('Applying', fn)
            try:
                client.query(stmt, validate=False)
                record_migration(client, fn)
            except Exception as e:
                print('Failed to apply', fn, e)
                raise


if __name__ == '__main__':
    apply_all()
