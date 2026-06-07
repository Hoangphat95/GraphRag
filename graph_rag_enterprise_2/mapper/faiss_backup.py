import os
import shutil
import datetime
import logging

logger = logging.getLogger(__name__)


def backup(index_path: str, meta_path: str, dest_dir: str) -> dict:
    """Copy FAISS index and meta files into `dest_dir` with a timestamp suffix.

    Returns dict with keys: index, meta, timestamp (paths or None).
    """
    os.makedirs(dest_dir, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    def copy_if_exists(src: str, basename: str):
        if src and os.path.exists(src):
            dst = os.path.join(dest_dir, f"{basename}.{ts}")
            shutil.copy2(src, dst)
            return dst
        return None

    idx_dst = copy_if_exists(index_path, "faiss.index")
    meta_dst = copy_if_exists(meta_path, "faiss_meta.pkl")
    logger.info("FAISS backup created: %s %s", idx_dst, meta_dst)
    return {"index": idx_dst, "meta": meta_dst, "timestamp": ts}


def restore(index_backup_path: str, meta_backup_path: str, target_index_path: str, target_meta_path: str) -> dict:
    """Restore backed-up files to target paths. Returns dict with final paths."""
    # ensure target dirs exist
    for p in (target_index_path, target_meta_path):
        d = os.path.dirname(p)
        if d:
            os.makedirs(d, exist_ok=True)

    if index_backup_path:
        shutil.copy2(index_backup_path, target_index_path)
    if meta_backup_path:
        shutil.copy2(meta_backup_path, target_meta_path)

    logger.info("FAISS restore completed -> %s , %s", target_index_path, target_meta_path)
    return {"index": target_index_path, "meta": target_meta_path}
