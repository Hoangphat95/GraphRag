FAISS Migration Helper

Usage

- Build a FAISS index from existing `embeddings.npy` (saved by `EmbeddingMatcher`).

Commands:

```bash
python mapper/faiss_migration.py --index-path data/faiss.index --meta-path data/faiss_meta.pkl
```

Options:
- `--force`: overwrite existing index
- `--no-meta`: do not write metadata file

Notes

- The script will attempt to import `mapper.embedding_matcher.EmbeddingMatcher` to capture `keys`/`values` ordering for reliable index→property mapping. If that import fails, it will fallback to `values.pkl` if present.
- If you don't have `faiss` installed, the script will print a message and exit; install `faiss-cpu` or `faiss-gpu` as appropriate.
