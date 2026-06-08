# GraphRAG - Chatbot tư vấn lốp xe

Hệ thống **GraphRAG** (Graph + Retrieval Augmented Generation) kết hợp **Neo4j graph database** + **Gemini AI** để tư vấn lốp xe thông minh. Hỗ trợ tra cứu thông số kỹ thuật, so sánh sản phẩm, và trả lời các câu hỏi về lốp xe bằng tiếng Việt.

---

## 🚀 Quick Start

### Yêu cầu
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (package manager)

### 1. Cài đặt

```bash
uv sync
```

### 2. Cấu hình

Tạo file `.env` (đã có sẵn trong dự án):

```env
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=your-username
NEO4J_PASSWORD=your-password
GEMINI_API_KEY=your-gemini-api-key
NEO4J_DATABASE=your-database
```

### 3. Chạy server

```bash
make dev
```

Hoặc click đúp `dev.bat`.

Mở trình duyệt: **http://localhost:8000**

---

## 📋 Commands

| Lệnh | Chức năng |
|---|---|
| `make dev` | Chạy dev với hot-reload |
| `make run` | Chạy production |
| `make test` | Chạy test |
| `make lint` | Kiểm tra code style (ruff) |
| `make shell` | Mở Python shell |
| `make clean` | Xoá __pycache__ |

---

## 🏗 Kiến trúc

```
User Query
    │
    ▼
┌─────────────────────────────┐
│     FastAPI (main.py)       │
│  APIKeyAuth + RateLimit MW  │
│  Prometheus + OTEL tracing  │
└──────────┬──────────────────┘
           │ GET /query?q=...
           ▼
┌─────────────────────────────┐
│   GraphRAGv3 (orchestrator) │  ← Pipeline chính (6 bước)
└──────────┬──────────────────┘
           │
      ┌────┴────┬────┬────┬────┐
      ▼         ▼    ▼    ▼    ▼
   RETRIEVE   PLAN  EXEC  REASON ANSWER
```

### Luồng xử lý

| Bước | Module | Chức năng |
|---|---|---|
| **1. RETRIEVE** | `HybridRetriever` | Trích xuất thông tin từ câu hỏi (rule-based + embedding) |
| **2. CONTEXT** | `ContextManager` | Xử lý hội thoại nhiều lượt (Redis/memory) |
| **3. PLAN** | `QueryPlanner` | Xác định ý định: SPEED, LOAD, PRICE, COMPARE... |
| **4. EXECUTE** | `CypherBuilder` / `CypherGenerator` | Truy vấn Neo4j (template ưu tiên, LLM fallback) |
| **5. REASON** | `ResultReasoner` | Suy luận kết quả, so sánh, sort |
| **6. ANSWER** | `AnswerGenerator` | Tạo câu trả lời (rule-based + emoji, LLM fallback) |

### Cấu trúc thư mục

```
app/
├── main.py                  # FastAPI app, routes, middleware
├── config.py                # Biến môi trường (dotenv)
├── neo4j.py                 # Neo4j service (Aura cloud)
├── llm_client.py            # Gemini LLM client
├── answer.py                # AnswerGenerator (rule-based + LLM)
├── context.py               # Context multi-turn (Redis/memory)
├── normalizer.py            # Chuẩn hoá key DB
├── intent_classifier.py     # ML intent fallback
├── metrics.py               # Prometheus metrics
├── tracing.py               # OpenTelemetry tracing
├── middleware.py             # API Key + Rate limit
│
├── pipeline/
│   └── orchestrator.py      # GraphRAGv3 — pipeline chính
│
├── retriever/
│   ├── hybrid_retriever.py  # Gộp mapper + embedding
│   ├── mapper.py            # Rule-based mapping
│   ├── value_store.py       # Cache giá trị từ Neo4j
│   ├── embedding_matcher.py # SentenceTransformer + FAISS
│   ├── planner.py           # QueryPlanner
│   └── model_manager.py     # Load model AI
│
├── cypher/
│   ├── cypher_builder.py    # Sinh Cypher tĩnh
│   ├── cypher_generator.py  # Sinh Cypher bằng LLM
│   ├── validator.py         # Kiểm tra Cypher an toàn
│   ├── value_mapper.py      # Query → column/value
│   ├── property_normalizer.py # Synonym map
│   ├── prompt_cypher.py     # Prompt cho LLM sinh Cypher
│   ├── tool_calling.py      # LLM + validate Cypher
│   ├── audit.py             # Log Cypher
│   ├── limits.py            # LIMIT policy
│   └── graph_schema.json    # Schema Neo4j
│
├── reasoner/
│   └── result_reasoner.py   # Suy luận dữ liệu
│
├── mapper/                  # Data files (embeddings, value_store)
│
└── backup/                  # Scripts khởi tạo DB
    ├── extract_schema.py    # Dump schema Neo4j
    ├── apply_migrations.py  # Apply migration
    ├── check_neo4j.py       # Kiểm tra index
    └── wait_for_neo4j.py    # Chờ Neo4j ready
```

---

## 🔌 API Endpoints

| Method | Route | Chức năng |
|---|---|---|
| GET | `/` | Trang chủ |
| GET | `/query?q=...` | Chat với bot |
| GET | `/health` | Kiểm tra health |
| GET | `/metrics` | Prometheus metrics |
| POST | `/reset` | Reset context |

### Ví dụ

```bash
# Hỏi thông tin lốp
curl "http://localhost:8000/query?q=lốp%20120/70-17%20giá%20bao%20nhiêu"

# Response
{
  "query": "lốp 120/70-17 giá bao nhiêu",
  "answer": "💰 Lốp 120/70-17 có giá 450,000 VNĐ.",
  "plan": {"type": "PRICE", "sizes": ["120/70-17"]}
}
```

---

## 🧪 Chạy test

```bash
make test
```

Hoặc gõ tay:
```bash
uv run pytest tests -q -x --timeout=30
```

---

## 🐳 Docker

```bash
docker-compose up -d
```

Hoặc dùng Docker stack production:
```bash
docker compose -f infra/docker/docker-compose.prod.yml up -d
```

---

## 🌐 Công nghệ sử dụng

| Công nghệ | Mục đích |
|---|---|
| **FastAPI** | REST API framework |
| **Neo4j Aura** | Graph database (cloud) |
| **Gemini AI** | LLM sinh Cypher + câu trả lời |
| **SentenceTransformer** | Embedding semantic matching |
| **FAISS** | Vector search (tùy chọn) |
| **Redis** | Context multi-turn (tùy chọn) |
| **Prometheus** | Metrics & monitoring |
| **OpenTelemetry** | Distributed tracing (tùy chọn) |

---

## 📁 Tài liệu tham khảo

Tài liệu chi tiết nằm trong thư mục `docs/`:

- [Cấu trúc code cũ](docs/README_structure.md)
- [Tracing & OpenTelemetry](docs/README_TRACING.md)
- [Monitoring](docs/monitoring.md)
- [Neo4j hardening](docs/neo4j_hardening.md)
- [FAISS setup](docs/faiss.md)
- [Secrets management](docs/secrets.md)
