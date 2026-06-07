=== FILE: graph_rag_enterprise_2/api/app.py ===
Lines: 301
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pipeline.orchestrator_v3 import GraphRAGv3
import re

---
=== FILE: graph_rag_enterprise_2/config/settings.py ===
Lines: 7
import os

# Read Neo4j connection info from environment for security (do NOT hardcode secrets)
# Example: export NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_URI = os.environ.get("NEO4J_URI", "neo4j://127.0.0.1:7687")
---
=== FILE: graph_rag_enterprise_2/core/context_manager.py ===
Lines: 36
class ContextManager:

    def __init__(self):
        self.history = []

---
=== FILE: graph_rag_enterprise_2/core/retry.py ===
Lines: 9
# core/retry.py
import time

def retry(func, retries=3):
    for i in range(retries):
---
=== FILE: graph_rag_enterprise_2/cypher/cypher_builder.py ===
Lines: 291
import re
from .limits import SINGLE_LIMIT, MULTI_LIMIT

class CypherBuilder:

---
=== FILE: graph_rag_enterprise_2/cypher/cypher_generator.py ===
Lines: 174
import os
import json
import logging
import re
from llm.llm_client import LLMClient
---
=== FILE: graph_rag_enterprise_2/cypher/limits.py ===
Lines: 7
"""Centralized LIMIT policy for Cypher queries."""

# single-value queries
SINGLE_LIMIT = 1

---
=== FILE: graph_rag_enterprise_2/cypher/metrics.py ===
Lines: 27
import threading
from collections import defaultdict

_lock = threading.Lock()
_counters = defaultdict(int)
---
=== FILE: graph_rag_enterprise_2/cypher/property_normalizer.py ===
Lines: 89
import unicodedata


class PropertyNormalizer:

---
=== FILE: graph_rag_enterprise_2/cypher/value_mapper.py ===
Lines: 182
import re
import unicodedata
from mapper.value_store import ValueStore, normalize_text

def normalize_query(text: str):
---
=== FILE: graph_rag_enterprise_2/db/kg_loader.py ===
Lines: 105
from db.neo4j_client import Neo4jClient
from functools import lru_cache


class KGLoader:
---
=== FILE: graph_rag_enterprise_2/db/neo4j_client.py ===
Lines: 102
import time
import logging
import os
from neo4j import GraphDatabase
from config.settings import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
---
=== FILE: graph_rag_enterprise_2/db/query_cache.py ===
Lines: 11
# # db/query_cache.py
# import hashlib

# class QueryCache:
#     def __init__(self):
---
=== FILE: graph_rag_enterprise_2/demo_ml_intent.py ===
Lines: 83
#!/usr/bin/env python3
"""
Demo: Graph RAG with ML Intent Classification
Hiển thị sự khác biệt giữa rule-based và ML-based intent detection
"""
---
=== FILE: graph_rag_enterprise_2/infra/logger.py ===
Lines: 6
# infra/logger.py
import logging

logging.basicConfig(level=logging.INFO)

---
=== FILE: graph_rag_enterprise_2/infra/metrics.py ===
Lines: 38
import time
import logging

logger = logging.getLogger(__name__)

---
=== FILE: graph_rag_enterprise_2/infra/tracing.py ===
Lines: 9
# infra/tracing.py
import time

def trace(func):
    def wrapper(*args, **kwargs):
---
=== FILE: graph_rag_enterprise_2/llm/__init__.py ===
Lines: 0
---
=== FILE: graph_rag_enterprise_2/llm/answer_generator.py ===
Lines: 442
from llm.llm_client import LLMClient
from utils.normalizer import normalize_data
import re

class AnswerGenerator:
---
=== FILE: graph_rag_enterprise_2/llm/intent_classifier.py ===
Lines: 458
"""
llm/intent_classifier.py  — REWRITE v2
========================================
Thay đổi so với v1:
  1. Bỏ BERT multilingual (680MB, chậm, overkill)
---
=== FILE: graph_rag_enterprise_2/llm/llm_client.py ===
Lines: 51
import os
from dotenv import load_dotenv
from google import genai
import time

---
=== FILE: graph_rag_enterprise_2/llm/prompt_answer.py ===
Lines: 24
def build_answer_prompt(query, data):

    return f"""
Bạn là chuyên gia bán lốp xe thực tế tại cửa hàng.

---
=== FILE: graph_rag_enterprise_2/llm/prompt_cypher.py ===
Lines: 32
def build_cypher_prompt(query, schema, detected_size=None):
    """Build a strict prompt for the LLM.

    If `detected_size` is provided, instruct the model to include
    `WHERE t.size = "{detected_size}"` in the Cypher.
---
=== FILE: graph_rag_enterprise_2/llm/tool_calling.py ===
Lines: 2
# llm/tool_calling.py
def tool_cypher(query):
    return f"CALL CYPHER FOR: {query}"---
=== FILE: graph_rag_enterprise_2/mapper/embedding_matcher.py ===
Lines: 114
from mapper.model_manager import get_model
import numpy as np
import re
import difflib

---
=== FILE: graph_rag_enterprise_2/mapper/mapper.py ===
Lines: 14
from cypher.value_mapper import ValueMapper as CypherValueMapper

class Mapper:

    def __init__(self):
---
=== FILE: graph_rag_enterprise_2/mapper/model_manager.py ===
Lines: 16
try:
    from sentence_transformers import SentenceTransformer
except Exception as e:
    SentenceTransformer = None
    MODEL_IMPORT_ERROR = e
---
=== FILE: graph_rag_enterprise_2/mapper/value_store.py ===
Lines: 132
import unicodedata
import os
import pickle

import sys
---
=== FILE: graph_rag_enterprise_2/pipeline/orchestrator_v3.py ===
Lines: 310
from retriever.hybrid_retriever import HybridRetriever
from planner.query_planner import QueryPlanner
from cypher.cypher_builder import CypherBuilder
from cypher.cypher_generator import CypherGenerator
from validation.cypher_validator import CypherValidator
---
=== FILE: graph_rag_enterprise_2/pipeline/rag_pipeline.py ===
Lines: 119
from mapper.mapper import Mapper
from cypher.cypher_builder import CypherBuilder
from cypher.cypher_generator import CypherGenerator
from validation.cypher_validator import CypherValidator
from db.neo4j_client import Neo4jClient
---
=== FILE: graph_rag_enterprise_2/planner/__init__.py ===
Lines: 0
---
=== FILE: graph_rag_enterprise_2/planner/query_planner.py ===
Lines: 192
from llm.intent_classifier import IntentClassifier
import os

class QueryPlanner:

---
=== FILE: graph_rag_enterprise_2/reasoner/result_reasoner.py ===
Lines: 222
class ResultReasoner:

    def reason(self, query, data, plan_type=None):

        # =========================
---
=== FILE: graph_rag_enterprise_2/recommender/context_parser.py ===
Lines: 40
import re

class ContextParser:

    def parse(self, query: str):
---
=== FILE: graph_rag_enterprise_2/recommender/explanation_generator.py ===
Lines: 8
class ExplanationGenerator:

    def generate(self, tire, reasons):
        explain = f"Lốp {tire.get('size')} ({tire.get('brand')}) được chọn vì:\n"

---
=== FILE: graph_rag_enterprise_2/recommender/scoring_engine.py ===
Lines: 39
class ScoringEngine:

    def score(self, tire, context):
        score = 0
        reasons = []
---
=== FILE: graph_rag_enterprise_2/recommender/tire_recommender.py ===
Lines: 103
from db.neo4j_client import Neo4jClient
from recommender.context_parser import ContextParser
from recommender.scoring_engine import ScoringEngine
from recommender.explanation_generator import ExplanationGenerator

---
=== FILE: graph_rag_enterprise_2/retriever/hybrid_retriever.py ===
Lines: 26
from mapper.mapper import Mapper
from mapper.embedding_matcher import EmbeddingMatcher

class HybridRetriever:

---
=== FILE: graph_rag_enterprise_2/router/auto_learner.py ===
Lines: 85
import json
import os


class AutoLearner:
---
=== FILE: graph_rag_enterprise_2/router/ml_router.py ===
Lines: 91
import os
import pickle
import numpy as np
from mapper.model_manager import get_model

---
=== FILE: graph_rag_enterprise_2/router/rule_router.py ===
Lines: 38
import re

class RuleRouter:
    def __init__(self):
        self.size_pattern = re.compile(
---
=== FILE: graph_rag_enterprise_2/tests/test_answer_generator.py ===
Lines: 21
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
---
=== FILE: graph_rag_enterprise_2/tests/test_cypher_size_where.py ===
Lines: 24
import re

from graph_rag_enterprise.cypher.cypher_builder import CypherBuilder
from graph_rag_enterprise.cypher.cypher_generator import CypherGenerator

---
=== FILE: graph_rag_enterprise_2/tests/test_intent_classifier.py ===
Lines: 44
#!/usr/bin/env python3
"""
Test Intent Classifier integration
"""

---
=== FILE: graph_rag_enterprise_2/tests/test_models.py ===
Lines: 17
import os
import pytest

# This test calls external API; skip by default unless explicitly enabled.
if os.getenv("RUN_EXTERNAL_TESTS") != "1" or not os.getenv("GEMINI_API_KEY"):
---
=== FILE: graph_rag_enterprise_2/tests/test_neo4j_client.py ===
Lines: 104
import types
import pytest


class FakeRecord:
---
=== FILE: graph_rag_enterprise_2/tests/test_pipeline.py ===
Lines: 90
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
---
=== FILE: graph_rag_enterprise_2/tests/test_stress_conversation.py ===
Lines: 62
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
---
=== FILE: graph_rag_enterprise_2/training/builders/context_recommend_builder.py ===
Lines: 121
# training/builders/context_recommend_builder.py

import random


---
=== FILE: graph_rag_enterprise_2/training/builders/data_builder_pro.py ===
Lines: 189
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
---
=== FILE: graph_rag_enterprise_2/training/builders/hard_negative_builder.py ===
Lines: 38
import random

class HardNegativeBuilder:

    def __init__(self):
---
=== FILE: graph_rag_enterprise_2/training/builders/paraphrase_generator.py ===
Lines: 25
import random

class ParaphraseGenerator:

    def __init__(self):
---
=== FILE: graph_rag_enterprise_2/training/train_intent_classifier.py ===
Lines: 104
#!/usr/bin/env python3
"""
training/train_intent_classifier.py  — v2
==========================================
Chạy: python training/train_intent_classifier.py
---
=== FILE: graph_rag_enterprise_2/training/train_multitask.py ===
Lines: 76
import json
import pickle
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
---
=== FILE: graph_rag_enterprise_2/utils/normalizer.py ===
Lines: 22
def normalize_record(rec: dict) -> dict:
    if not isinstance(rec, dict):
        return rec
    nr = dict(rec)
    # canonical aliases
---
=== FILE: graph_rag_enterprise_2/validation/cypher_validator.py ===
Lines: 121
import os
import re
import json


---
=== FILE: graph_rag_enterprise_2/validation/guardrails.py ===
Lines: 3
# validation/guardrails.py
def check_dangerous_query(cypher):
    banned = ["DELETE", "DROP", "REMOVE"]
    return not any(b in cypher.upper() for b in banned)---
=== FILE: graph_rag_enterprise_2/validation/schema_checker.py ===
Lines: 9
class SchemaChecker:

    def __init__(self, schema):
        self.schema = schema

---
=== graph_rag_enterprise_2/api/app.py ===
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pipeline.orchestrator_v3 import GraphRAGv3
import re
def markdown_to_html(text):
def home():
def query(q: str):
def reset_context():

=== graph_rag_enterprise_2/config/settings.py ===
import os

=== graph_rag_enterprise_2/core/context_manager.py ===
class ContextManager:

=== graph_rag_enterprise_2/core/retry.py ===
import time
def retry(func, retries=3):

=== graph_rag_enterprise_2/cypher/cypher_builder.py ===
import re
from .limits import SINGLE_LIMIT, MULTI_LIMIT
class CypherBuilder:

=== graph_rag_enterprise_2/cypher/cypher_generator.py ===
import os
import json
import logging
import re
from llm.llm_client import LLMClient
from llm.prompt_cypher import build_cypher_prompt
from validation.cypher_validator import CypherValidator
from .limits import SINGLE_LIMIT, MULTI_LIMIT
from . import metrics
class CypherGenerator:

=== graph_rag_enterprise_2/cypher/limits.py ===

=== graph_rag_enterprise_2/cypher/metrics.py ===
import threading
from collections import defaultdict
def increment(name: str, amount: int = 1):
def get_metrics():
def reset_metrics():
def dump_to_file(path: str):

=== graph_rag_enterprise_2/cypher/property_normalizer.py ===
import unicodedata
class PropertyNormalizer:

=== graph_rag_enterprise_2/cypher/value_mapper.py ===
import re
import unicodedata
from mapper.value_store import ValueStore, normalize_text
def normalize_query(text: str):
def find_exact_match(candidate: str, data):
def find_best_column(query_part: str, columns):
def clean_text(text: str):
def extract_candidates(query: str):
class ValueMapper:

=== graph_rag_enterprise_2/db/kg_loader.py ===
from db.neo4j_client import Neo4jClient
from functools import lru_cache
class KGLoader:

=== graph_rag_enterprise_2/db/neo4j_client.py ===
import time
import logging
import os
from neo4j import GraphDatabase
from config.settings import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from validation.cypher_validator import CypherValidator
from utils.normalizer import normalize_data
class Neo4jClient:

=== graph_rag_enterprise_2/db/query_cache.py ===

=== graph_rag_enterprise_2/demo_ml_intent.py ===
import sys
import os
from llm.intent_classifier import IntentClassifier
def demo_ml_intent():

=== graph_rag_enterprise_2/infra/logger.py ===
import logging
def log(msg):

=== graph_rag_enterprise_2/infra/metrics.py ===
import time
import logging
class Metrics:

=== graph_rag_enterprise_2/infra/tracing.py ===
import time
def trace(func):

=== graph_rag_enterprise_2/llm/__init__.py ===

=== graph_rag_enterprise_2/llm/answer_generator.py ===
from llm.llm_client import LLMClient
from utils.normalizer import normalize_data
import re
class AnswerGenerator:

=== graph_rag_enterprise_2/llm/intent_classifier.py ===
import os
import json
import pickle
import numpy as np
from typing import Dict, List
def _get_embedder():
def _get_lr():
class IntentClassifier:
def _augment(query: str) -> List[str]:
def _softmax(x):

=== graph_rag_enterprise_2/llm/llm_client.py ===
import os
from dotenv import load_dotenv
from google import genai
import time
class LLMClient:

=== graph_rag_enterprise_2/llm/prompt_answer.py ===
def build_answer_prompt(query, data):

=== graph_rag_enterprise_2/llm/prompt_cypher.py ===
def build_cypher_prompt(query, schema, detected_size=None):

=== graph_rag_enterprise_2/llm/tool_calling.py ===
def tool_cypher(query):

=== graph_rag_enterprise_2/mapper/embedding_matcher.py ===
from mapper.model_manager import get_model
import numpy as np
import re
import difflib
class EmbeddingMatcher:

=== graph_rag_enterprise_2/mapper/mapper.py ===
from cypher.value_mapper import ValueMapper as CypherValueMapper
class Mapper:

=== graph_rag_enterprise_2/mapper/model_manager.py ===
def get_model():

=== graph_rag_enterprise_2/mapper/value_store.py ===
import unicodedata
import os
import pickle
import sys
import os
from db.neo4j_client import Neo4jClient
def normalize_text(text: str):
class ValueStore:

=== graph_rag_enterprise_2/pipeline/orchestrator_v3.py ===
from retriever.hybrid_retriever import HybridRetriever
from planner.query_planner import QueryPlanner
from cypher.cypher_builder import CypherBuilder
from cypher.cypher_generator import CypherGenerator
from validation.cypher_validator import CypherValidator
from db.neo4j_client import Neo4jClient
from reasoner.result_reasoner import ResultReasoner
from llm.answer_generator import AnswerGenerator
from core.context_manager import ContextManager
from utils.normalizer import normalize_data
import unicodedata
class GraphRAGv3:

=== graph_rag_enterprise_2/pipeline/rag_pipeline.py ===
from mapper.mapper import Mapper
from cypher.cypher_builder import CypherBuilder
from cypher.cypher_generator import CypherGenerator
from validation.cypher_validator import CypherValidator
from db.neo4j_client import Neo4jClient
from llm.answer_generator import AnswerGenerator
from infra.metrics import Metrics
from mapper.embedding_matcher import EmbeddingMatcher
from router.ml_router import MLRouter
from router.rule_router import RuleRouter
from recommender.tire_recommender import SmartRecommender
class RAGPipeline:

=== graph_rag_enterprise_2/planner/__init__.py ===

=== graph_rag_enterprise_2/planner/query_planner.py ===
from llm.intent_classifier import IntentClassifier
import os
class QueryPlanner:

=== graph_rag_enterprise_2/reasoner/result_reasoner.py ===
class ResultReasoner:

=== graph_rag_enterprise_2/recommender/context_parser.py ===
import re
class ContextParser:

=== graph_rag_enterprise_2/recommender/explanation_generator.py ===
class ExplanationGenerator:

=== graph_rag_enterprise_2/recommender/scoring_engine.py ===
class ScoringEngine:

=== graph_rag_enterprise_2/recommender/tire_recommender.py ===
from db.neo4j_client import Neo4jClient
from recommender.context_parser import ContextParser
from recommender.scoring_engine import ScoringEngine
from recommender.explanation_generator import ExplanationGenerator
class SmartRecommender:

=== graph_rag_enterprise_2/retriever/hybrid_retriever.py ===
from mapper.mapper import Mapper
from mapper.embedding_matcher import EmbeddingMatcher
class HybridRetriever:

=== graph_rag_enterprise_2/router/auto_learner.py ===
import json
import os
class AutoLearner:

=== graph_rag_enterprise_2/router/ml_router.py ===
import os
import pickle
import numpy as np
from mapper.model_manager import get_model
class MLRouter:

=== graph_rag_enterprise_2/router/rule_router.py ===
import re
class RuleRouter:

=== graph_rag_enterprise_2/tests/test_answer_generator.py ===
import sys
import os
from llm.answer_generator import AnswerGenerator
def test_format_compare_returns_markdown():

=== graph_rag_enterprise_2/tests/test_cypher_size_where.py ===
import re
from graph_rag_enterprise.cypher.cypher_builder import CypherBuilder
from graph_rag_enterprise.cypher.cypher_generator import CypherGenerator
def test_cypher_builder_single_includes_where_for_size():
def test_cypher_generator_fallback_includes_where_for_size():

=== graph_rag_enterprise_2/tests/test_intent_classifier.py ===
import sys
import os
from llm.intent_classifier import IntentClassifier
def test_intent_classifier():

=== graph_rag_enterprise_2/tests/test_models.py ===
import os
import pytest
from google import genai
from dotenv import load_dotenv

=== graph_rag_enterprise_2/tests/test_neo4j_client.py ===
import types
import pytest
class FakeRecord:
class FakeSession:
class FakeDriver:
def test_query_passes_params_and_returns_data(monkeypatch):
def test_query_retries_on_failure(monkeypatch):
def test_check_indexes_reports_missing(monkeypatch):

=== graph_rag_enterprise_2/tests/test_pipeline.py ===
import sys
import os
from pipeline.orchestrator_v3 import GraphRAGv3

=== graph_rag_enterprise_2/tests/test_stress_conversation.py ===
import os
import sys
import time
from pipeline.orchestrator_v3 import GraphRAGv3
def test_stress_conversation():

=== graph_rag_enterprise_2/training/builders/context_recommend_builder.py ===
import random
class ContextRecommendBuilder:

=== graph_rag_enterprise_2/training/builders/data_builder_pro.py ===
import sys
import os
import json
import random
from collections import defaultdict
from db.kg_loader import KGLoader
class DataBuilder:

=== graph_rag_enterprise_2/training/builders/hard_negative_builder.py ===
import random
class HardNegativeBuilder:

=== graph_rag_enterprise_2/training/builders/paraphrase_generator.py ===
import random
class ParaphraseGenerator:

=== graph_rag_enterprise_2/training/train_intent_classifier.py ===
import sys
import os
from llm.intent_classifier import IntentClassifier
from sklearn.model_selection import train_test_split
import json
def main():

=== graph_rag_enterprise_2/training/train_multitask.py ===
import json
import pickle
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
class MultiTaskModel:

=== graph_rag_enterprise_2/utils/normalizer.py ===
def normalize_record(rec: dict) -> dict:
def normalize_data(data):

=== graph_rag_enterprise_2/validation/cypher_validator.py ===
import os
import re
import json
class CypherValidator:

=== graph_rag_enterprise_2/validation/guardrails.py ===
def check_dangerous_query(cypher):

=== graph_rag_enterprise_2/validation/schema_checker.py ===
class SchemaChecker:

=== GRAPH SCHEMA ===
{
  "nodes": [
    "Tire",
    "TirePattern",
    "QualityStandard",
    "TireType",
    "Tube",
    "Brand",
    "Van",
    "Company"
  ],
  "relationships": [
    "CÓ_HOA",
    "THUỘC_NHÓM",
    "DÙNG_CHO",
    "CÓ_BIẾN_THỂ",
    "ĐẠT_CHUẨN",
    "SẢN_XUẤT_SĂM",
    "DÙNG_VAN",
    "CO_SP"
  ],
  "properties": {
    "Tire": [
      "kieu_quy_cach",
      "duong_kinh_ngoai",
      "co_sam",
      "tai_trong_lon_nhat",
      "chieu_rong_vanh",
      "gia_nhap_chua_vat",
      "toc_do_toi_da",
      "vehicle_type",
      "gia_nhap_co_vat",
      "kieu_hoa",
      "loai_xe_dap",
      "so_lop_bo",
      "duong_kinh_vanh",
      "rong_vanh_thich_hop",
      "nhom_lop",
      "phan_loai_tai",
      "gia_ban_co_vat",
      "gia_ban_chua_vat",
      "vanh",
      "chieu_rong_toan_bo",
      "chi_so_tai_toc_do",
      "cau_truc_lop",
      "noi_ap_tieu_chuan",
      "dong_series",
      "size",
      "chieu_sau_hoa",
      "brand",
      "rong_vanh_tieu_chuan"
    ],
    "TirePattern": [
      "pattern"
    ],
    "TireType": [
      "name"
    ],
    "Tube": [
      "vehicle_type",
      "chieu_day_gap_doi",
      "kieu_quy_cach",
      "size",
      "chieu_rong_gap_doi"
    ],
    "QualityStandard": [
      "name"
    ],
    "Brand": [
      "name"
    ],
    "Van": [
      "name"
    ],
    "Company": [
      "name"
    ]
  },
  "graph": [
    {
      "from": "Tire",
      "rel": "CÓ_HOA",
      "to": "TirePattern"
    },
    {
      "from": "Tire",
      "rel": "THUỘC_NHÓM",
      "to": "TireType"
    },
    {
      "from": "Tire",
      "rel": "CÓ_BIẾN_THỂ",
      "to": "TirePattern"
    },
    {
      "from": "Tire",
      "rel": "ĐẠT_CHUẨN",
      "to": "QualityStandard"
    },
    {
      "from": "Tube",
      "rel": "DÙNG_VAN",
      "to": "Van"
    },
    {
      "from": "Tube",
      "rel": "DÙNG_CHO",
      "to": "Tire"
    },
    {
      "from": "Brand",
      "rel": "SẢN_XUẤT_SĂM",
      "to": "Tube"
    },
    {
      "from": "Company",
      "rel": "CO_SP",
      "to": "Tire"
    }
  ]
}=== INTENT SCHEMA ===
{
  "version": "2.0",
  "description": "Intent schema đồng bộ với QueryPlanner và CypherBuilder",
  "intents": [
    {
      "name": "SINGLE",
      "description": "Hỏi thông tin tổng quát về 1 size lốp cụ thể",
      "examples": ["lốp 120/70-17 thông số thế nào", "lốp 2.50-17 có những gì"]
    },
    {
      "name": "SPEED",
      "description": "Hỏi tốc độ tối đa của 1 size cụ thể",
      "examples": ["lốp 120/70-17 tốc độ bao nhiêu", "2.50-17 chạy được bao nhiêu km/h"]
    },
    {
      "name": "MAX_SPEED",
      "description": "Hỏi lốp nào tốc độ cao nhất (không cần size cụ thể)",
      "examples": ["lốp nào chạy nhanh nhất", "tốc độ tối đa cao nhất là lốp nào"]
    },
    {
      "name": "LOAD",
      "description": "Hỏi tải trọng của 1 size cụ thể",
      "examples": ["lốp 2.50-17 chịu tải bao nhiêu", "120/70-17 tải trọng kg"]
    },
    {
      "name": "MAX_LOAD",
      "description": "Hỏi lốp nào chịu tải cao nhất",
      "examples": ["lốp nào chịu tải tốt nhất", "tải trọng lớn nhất là lốp nào"]
    },
    {
      "name": "PRICE",
      "description": "Hỏi giá của 1 size cụ thể",
      "examples": ["lốp 120/70-17 giá bao nhiêu", "2.50-17 bán bao nhiêu tiền"]
    },
    {
      "name": "MAX_PRICE",
      "description": "Hỏi lốp nào giá cao nhất hoặc rẻ nhất",
      "examples": ["lốp nào giá cao nhất", "lốp rẻ nhất là loại nào"]
    },
    {
      "name": "PRESSURE",
      "description": "Hỏi nội áp tiêu chuẩn (áp suất bơm)",
      "examples": ["lốp 120/70-17 bơm bao nhiêu bar", "áp suất tiêu chuẩn 2.50-17"]
    },
    {
      "name": "COMPARE",
      "description": "So sánh 2 hoặc nhiều size lốp",
      "examples": ["so sánh 100/80-14 và 110/80-14", "2.50-17 với 2.75-17 khác nhau gì"]
    },
    {
      "name": "MULTI_HOP",
      "description": "Hỏi thông tin qua graph traversal: hãng, tiêu chuẩn, van/săm",
      "examples": ["lốp 120/70-17 đạt tiêu chuẩn gì", "lốp 2.50-17 dùng van gì", "hãng nào sản xuất lốp 120/70-17"]
    },
    {
      "name": "RECOMMEND",
      "description": "Tư vấn, gợi ý lốp phù hợp theo xe hoặc nhu cầu sử dụng",
      "examples": ["tư vấn lốp đi đường dài", "xe Vision nên dùng lốp gì", "lốp phù hợp để đi phố"]
    },
    {
      "name": "NO_MATCH",
      "description": "Câu hỏi mơ hồ, thiếu context, không đủ thông tin để xử lý",
      "examples": ["lốp nào tốt nhất", "mẫu này thế nào", "loại nào dùng được"]
    }
  ]
}