# Graph RAG Enterprise 2 — Quick Start

Những thay đổi chính (an toàn hoá Text→Cypher): parameterized queries, validator, context persistence, LLM guardrails.

Environment variables
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` — kết nối Neo4j
- `NEO4J_AUTO_CREATE_INDEXES` (true/false) — tự tạo index khi khởi động (tùy chọn)
- `REDIS_URL` hoặc `REDIS_HOST`/`REDIS_PORT` — nếu muốn dùng Redis cho ContextManager và rate-limit
- `API_KEY` — nếu đặt, API yêu cầu header `x-api-key`
- `RATE_LIMIT_PER_MINUTE` — giới hạn theo IP (mặc định 60)
- `EMBEDDING_MATCH_THRESHOLD` — threshold cho embedding matcher (mặc định 0.65)
- `LLM_CYPHER_AUDIT_LOG` — đường dẫn log audit LLM→Cypher

Utilities
- `scripts/check_neo4j.py` — kiểm tra index Neo4j và gợi ý câu lệnh CREATE INDEX

Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # optional
export PYTHONPATH=.
uvicorn api.app:app --reload
```

Notes
- Tests are in `graph_rag_enterprise_2/tests` and CI workflow `.github/workflows/ci.yml` runs them.
- For production, use Redis for ContextManager and rate-limiter for multi-process scaling.
