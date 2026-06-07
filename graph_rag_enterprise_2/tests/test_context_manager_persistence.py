from core.context_manager import ContextManager


def test_context_manager_sqlite_add_and_get_last(tmp_path):
    db_file = tmp_path / "ctx.db"
    cm = ContextManager(backend='sqlite', db_path=str(db_file))

    cm.add_context('q1', [{'column': 'size', 'value': '120/70-17'}], {'type': 'SINGLE'}, [{'size': '120/70-17'}])
    last = cm.get_last()
    assert last is not None
    assert last['query'] == 'q1'
    assert any(m.get('column') == 'size' for m in last['mapped'])


def test_get_last_size_from_history():
    cm = ContextManager(backend='memory')
    cm.add_context('q1', [{'column': 'size', 'value': '120/70-17'}], {}, [])
    cm.add_context('q2', [{'column': 'size', 'value': '110/70-17'}], {}, [])
    last_size = cm.get_last_size()
    assert last_size in ['120/70-17', '110/70-17']
