import os
import pytest

if os.environ.get('RUN_INTEGRATION') != '1':
    pytest.skip('Skipping Neo4j integration tests', allow_module_level=True)

from db.neo4j_client import Neo4jClient


def test_neo4j_ping_and_indexes():
    client = Neo4jClient()
    missing = client.check_indexes()
    # check_indexes returns list (may be empty) — assert it returns a list
    assert isinstance(missing, list)
