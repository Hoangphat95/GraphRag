import types
import pytest


class FakeRecord:
    def __init__(self, data):
        self._data = data

    def data(self):
        return self._data


class FakeSession:
    def __init__(self, run_impl):
        self._run_impl = run_impl

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def run(self, cypher, params=None, timeout=None):
        return self._run_impl(cypher, params, timeout)


class FakeDriver:
    def __init__(self, run_impl):
        self._run_impl = run_impl

    def session(self):
        return FakeSession(self._run_impl)

    def close(self):
        pass


def test_query_passes_params_and_returns_data(monkeypatch):
    calls = {}

    def run_impl(cypher, params, timeout):
        calls['cypher'] = cypher
        calls['params'] = params
        calls['timeout'] = timeout
        return [FakeRecord({'a': 1}), FakeRecord({'a': 2})]

    fake_driver = FakeDriver(run_impl)

    import graph_rag_enterprise.db.neo4j_client as nc

    monkeypatch.setattr(nc.GraphDatabase, 'driver', lambda *a, **k: fake_driver)

    client = nc.Neo4jClient(max_retries=0, query_timeout=5)
    res = client.query("MATCH (n) RETURN n", params={'limit': 2})

    assert isinstance(res, list)
    assert res[0]['a'] == 1
    assert calls['params'] == {'limit': 2}


def test_query_retries_on_failure(monkeypatch):
    state = {'calls': 0}

    def run_impl(cypher, params, timeout):
        state['calls'] += 1
        if state['calls'] == 1:
            raise Exception("transient")
        return [FakeRecord({'ok': True})]

    fake_driver = FakeDriver(run_impl)

    import graph_rag_enterprise.db.neo4j_client as nc

    monkeypatch.setattr(nc.GraphDatabase, 'driver', lambda *a, **k: fake_driver)

    client = nc.Neo4jClient(max_retries=1, query_timeout=5)
    res = client.query("MATCH (n) RETURN n")

    assert res[0]['ok'] is True
    assert state['calls'] == 2


def test_check_indexes_reports_missing(monkeypatch):
    def run_impl(cypher, params, timeout):
        # simulate db.indexes() returning empty set
        class R:
            def __init__(self):
                self._m = {}

            def data(self):
                return {}

        return []

    fake_driver = FakeDriver(run_impl)

    import graph_rag_enterprise.db.neo4j_client as nc

    monkeypatch.setattr(nc.GraphDatabase, 'driver', lambda *a, **k: fake_driver)

    client = nc.Neo4jClient(max_retries=0)
    missing = client.check_indexes(required=[('Tire', 'size'), ('Tire', 'brand')])

    assert ('Tire', 'size') in missing
