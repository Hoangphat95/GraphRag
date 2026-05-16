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
    def __init__(self, debug=True):
        self.mapper = Mapper()
        self.builder = CypherBuilder()
        self.generator = CypherGenerator()
        self.validator = CypherValidator()
        self.db = Neo4jClient()
        self.answer_llm = AnswerGenerator()
        self.metrics = Metrics()
        self.embed_matcher = EmbeddingMatcher()

        self.ml_router = MLRouter()
        self.rule_router = RuleRouter()
        self.recommender = SmartRecommender(self.db, self.answer_llm)

        self.debug = debug

    def _log(self, title, data):
        if self.debug:
            print(f"\n===== {title} =====")
            print(data)
            
    def fast_answer(self, query, result, intent):
        if not result:
            return None

        # ❌ KHÔNG fast nếu là query cần logic
        if intent in ["PRICE", "COMPARE"]:
            return None

        if len(result) == 1 and "result" in result[0]:
            return f"Kết quả: {result[0]['result']}"

        return None

    def run(self, query: str):
        start = self.metrics.start_timer()

        # 1. ML ROUTER
        pred = self.ml_router.predict(query)
        intent = pred["intent"]
        route = pred["route"]
        confidence = pred["confidence"]

        self._log("ML", pred)

        # 2. RULE FALLBACK
        if confidence < 0.6:
            rule = self.rule_router.route(query)
            if rule:
                route = rule["route"]
                intent = rule.get("intent", intent)
                self._log("FALLBACK RULE", rule)

        # 3. RECOMMEND
        if intent == "RECOMMEND":
            return self.recommender.recommend(query)

        # 4. MAPPING
        mapped = self.mapper.map(query)

        if not any(r.get("type") == "column_detect" for r in mapped):
            prop = self.embed_matcher.match(query)
            if prop:
                mapped.append({
                    "type": "column_detect",
                    "column": prop
                })

        # 🔥 FORCE COLUMN THEO INTENT
        if intent == "PRICE":
            mapped.append({
                "type": "column_detect",
                "column": "gia_ban_co_vat"
            })

        # 5. CYPHER
        try:
            cypher = self.builder.build(mapped, query)

            if ("MATCH" not in cypher) or (intent == "COMPARE"):
                cypher = self.generator.generate(query)

            if not self.validator.validate(cypher):
                cypher = self.generator.generate(query)

            result = self.db.query(cypher)

        except Exception as e:
            return f"⚠️ Lỗi xử lý: {str(e)}"

        # 6. FAST ANSWER (đã fix)
        fast = self.fast_answer(query, result, intent)
        if fast:
            return fast

        # 7. FAIL SAFE
        if not result:
            return "Hiện chưa có dữ liệu phù hợp, bạn thử mô tả rõ hơn nhé."

        latency = self.metrics.end_timer(start)
        self.metrics.log(query, cypher, result, latency)

        return self.answer_llm.generate(query, result)