import tempfile
import os
from mapper.faiss_backup import backup, restore


def test_faiss_backup_and_restore(tmp_path):
    # create fake index and meta files
    idx = tmp_path / 'faiss.index'
    meta = tmp_path / 'faiss_meta.pkl'
    idx.write_text('index-data')
    meta.write_text('meta-data')

    dest = tmp_path / 'backups'
    res = backup(str(idx), str(meta), str(dest))
    assert res['index'] is not None
    assert res['meta'] is not None
    assert os.path.exists(res['index'])
    assert os.path.exists(res['meta'])

    # restore to new targets
    tgt_idx = tmp_path / 'restored' / 'faiss.index'
    tgt_meta = tmp_path / 'restored' / 'faiss_meta.pkl'
    out = restore(res['index'], res['meta'], str(tgt_idx), str(tgt_meta))
    assert os.path.exists(out['index'])
    assert os.path.exists(out['meta'])
    assert open(out['index']).read() == 'index-data'
    assert open(out['meta']).read() == 'meta-data'
