# FAISS index management

This project stores FAISS index files on disk and supports migration, backup and restore.

Kubernetes:
- Mount the `faiss-pvc` at `/app/data` (see `k8s/deployment-app.yaml`).
- FAISS index path: `/app/data/faiss.index`
- FAISS meta path: `/app/data/faiss_meta.pkl`

Backup & Restore (local):

- Backup:

```py
from mapper.faiss_backup import backup
backup('/app/data/faiss.index', '/app/data/faiss_meta.pkl', '/backups/faiss')
```

- Restore:

```py
from mapper.faiss_backup import restore
restore('/backups/faiss/faiss.index.20250101T000000Z', '/backups/faiss/faiss_meta.pkl.20250101T000000Z', '/app/data/faiss.index', '/app/data/faiss_meta.pkl')
```

Automated backups:
- Run a CronJob or external backup process that copies `/app/data` to object storage.
- Consider checksum and verification after copy.

Example CronJob (Kubernetes):

See `k8s/cronjob-faiss-backup.yaml` for a simple daily backup that runs a Python runner which copies the FAISS index and meta files into a timestamped folder under `/backups/faiss` mounted via a PVC.

Runner (container): `scripts/faiss_backup_runner.py` — this script reads `FAISS_INDEX_PATH`, `FAISS_META_PATH` and `FAISS_BACKUP_DIR` from the environment and writes timestamped backups.

Uploading to object storage:
- After the CronJob creates a backup folder, run a second job to upload the folder to object storage (S3, GCS) using `rclone` or an S3 client. Keep credentials in a Kubernetes `Secret` and mount them into the job.

Notes:
- PVC should be configured with an appropriate `storageClassName` in production; use `hostPath` or NFS for single-node clusters.
- For large indexes, use streaming transfer tools (rsync, rclone) to minimize downtime.
