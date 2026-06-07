"""Simple runner to create timestamped FAISS backups into a target folder.
This script is intended to be run inside the app container (mounted PVC at /app/data)
and will copy the index and meta files to the backup folder.
"""
import os
import time
from pathlib import Path

from mapper.faiss_backup import backup


def main():
    src_idx = os.environ.get('FAISS_INDEX_PATH', '/app/data/faiss.index')
    src_meta = os.environ.get('FAISS_META_PATH', '/app/data/faiss_meta.pkl')
    dest_base = os.environ.get('FAISS_BACKUP_DIR', '/backups/faiss')
    Path(dest_base).mkdir(parents=True, exist_ok=True)
    ts = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    dest = Path(dest_base) / ts
    dest.mkdir(parents=True, exist_ok=True)
    res = backup(src_idx, src_meta, str(dest))
    print("Backup created:", res)


if __name__ == '__main__':
    main()
