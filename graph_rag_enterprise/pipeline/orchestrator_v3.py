from retriever.hybrid_retriever import HybridRetriever
from planner.query_planner import QueryPlanner
from cypher.cypher_builder import CypherBuilder
from cypher.cypher_generator import CypherGenerator
from validation.cypher_validator import CypherValidator
from db.neo4j_client import Neo4jClient
from reasoner.result_reasoner import ResultReasoner
from llm.answer_generator import AnswerGenerator
from core.context_manager import ContextManager

import unicodedata


class GraphRAGv3:

    def __init__(self):
        self.retriever = HybridRetriever()
        self.planner = QueryPlanner()
        self.builder = CypherBuilder()
        self.validator = CypherValidator()
        self.db = Neo4jClient()
        self.reasoner = ResultReasoner()
        self.answer_generator = AnswerGenerator()
        self.context = ContextManager()

    def reset_context(self):
        self.context = ContextManager()

    def _normalize_text(self, text):
        if text is None:
            return ""

        normalized = str(text).lower().strip()
        normalized = unicodedata.normalize("NFD", normalized)
        normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        normalized = normalized.replace('đ', 'd')
        return normalized

    # =========================
    # FILTER DATA
    # =========================
    def filter_data_by_query(self, query, data, plan):
        q = query.lower()
        plan_type = plan.get("type") if plan else None

        if plan_type == "MAX_SPEED":
            return [
                {
                    "size": d.get("size"),
                    "max_speed": d.get("max_speed")
                }
                for d in data if "max_speed" in d
            ]

        if plan_type == "SPEED":
            return [
                {
                    "size": d.get("size"),
                    "speed": d.get("speed")
                }
                for d in data if "speed" in d
            ]

        if plan_type == "MAX_LOAD":
            return [
                {
                    "size": d.get("size"),
                    "max_load": d.get("max_load")
                }
                for d in data if "max_load" in d
            ]

        if plan_type == "LOAD":
            return [
                {
                    "size": d.get("size"),
                    "load": d.get("load")
                }
                for d in data if "load" in d
            ]

        if plan_type == "COMPARE":
            return data  # Giữ toàn bộ để so sánh

        if plan_type == "PRICE" or ("giá" in q):
            return [
                {
                    "size": d.get("size"),
                    "price": d.get("price") if "price" in d else d.get("gia_ban_co_vat")
                }
                for d in data if d.get("price") is not None or d.get("gia_ban_co_vat") is not None
            ]

        return data

    # =========================
    # FAST RULE ANSWER
    # =========================
    def fast_answer(self, query, data):
        q = query.lower()

        if "tốc độ" in q and len(data) == 1:
            d = data[0]
            if "speed" in d:
                return f"Lốp {d['size']} có tốc độ tối đa {d['speed']} km/h."
            if "max_speed" in d:
                return f"Lốp {d['size']} có tốc độ tối đa {d['max_speed']} km/h."

        if "cao nhất" in q and "tải" in q and len(data) == 1:
            d = data[0]
            if "max_load" in d:
                return f"Lốp {d['size']} chịu tải cao nhất: {d['max_load']} kg."

        if "chịu tải" in q and len(data) == 1:
            d = data[0]
            if "load" in d:
                return f"Lốp {d['size']} chịu tải tối đa {d['load']} kg."

        if len(data) == 1 and len(data[0]) == 1:
            return f"Kết quả: {list(data[0].values())[0]}"

        return None

    # =========================
    # MAIN RUN
    # =========================
    def run(self, query):

        print(f"\n🔍 Query: {query}")

        # =========================
        # RETRIEVE
        # =========================
        r = self.retriever.retrieve(query)
        mapped = r["mapped"]
        semantic = r.get("semantic")  # ← LẤY semantic từ retriever

        # =========================
        # CONTEXT RESOLUTION (Multi-turn)
        # =========================
        q = self._normalize_text(query)
        has_size = any(m.get("column") == "size" for m in mapped)
        last_size = self.context.get_last_size()
        last_sizes = self.context.get_last_sizes(2)

        followup_props = [
            "tốc độ", "tốc do", "chịu tải", "tải", "giá", "độ bền", "tiêu chuẩn", "van", "công ty", "áp suất"
        ]
        global_max_terms = ["cao nhat", "tot nhat", "max", "lon nhat", "nhieu nhat"]
        compare_followup = [
            "so sanh", "2 lop tren", "hai lop tren", "lop tren", "lop vua roi", "hai lop vua roi", "cai roi", "cai vua roi"
        ]
        referent_terms = ["no", "mau nay", "mau", "cai nay", "cai", "nó", "no", "nay"]

        if not has_size and last_size:
            if any(ref in q for ref in ["lop nay", "mau nay", "cai nay", "no", "do", "lop vua roi"]):
                mapped.append({"column": "size", "value": last_size, "type": "context"})
                print(f"\n✅ Context resolved size from previous query: {last_size}")
            elif any(term in q for term in followup_props) and not any(term in q for term in global_max_terms):
                mapped.append({"column": "size", "value": last_size, "type": "context"})
                print(f"\n✅ Follow-up property query resolved size from previous query: {last_size}")

        if has_size and last_size and any(term in q for term in compare_followup) and any(term in q for term in referent_terms):
            explicit_sizes = [m.get("value") for m in mapped if m.get("column") == "size"]
            if last_size not in explicit_sizes:
                mapped.append({"column": "size", "value": last_size, "type": "context"})
                print(f"\n✅ Compare follow-up resolved previous size from context: {last_size}")

        if not has_size and any(term in q for term in compare_followup) and len(last_sizes) >= 2:
            for size in last_sizes:
                mapped.append({"column": "size", "value": size, "type": "context"})
            print(f"\n✅ Compare follow-up resolved sizes from previous context: {last_sizes}")

        # =========================
        # SEMANTIC FALLBACK (TỐI ƯU #1)
        # =========================
        if semantic and not any(m.get("column") in ["size", "toc_do_toi_da", "tai_trong_lon_nhat", "gia_ban_co_vat"] for m in mapped):
            mapped.append({"column": semantic, "type": "semantic"})
            print(f"\n✅ Semantic enriched: {semantic}")

        print("\n===== MAPPED =====")
        print(mapped)

        # =========================
        # PLAN
        # =========================
        plan = self.planner.plan(query, mapped)

        print("\n===== PLAN =====")
        print(plan)

        # =========================
        # NO_MATCH DIRECT RESPONSE
        # =========================
        if plan.get("type") == "NO_MATCH":
            reason = self.reasoner.reason(query, [], plan.get("type"))
            if isinstance(reason, dict) and reason.get("message"):
                return reason["message"]
            return "Mình cần thêm thông tin để tư vấn chính xác hơn."

        # =========================
        # BUILD CYPHER
        # =========================
        cypher = self.builder.build(plan)

        # =========================
        # VALIDATE + LLM FALLBACK (TỐI ƯU #3)
        # =========================
        if not self.validator.validate(cypher):
            print("\n⚠️ Cypher invalid → try LLM fallback")
            gen = CypherGenerator()
            cypher = gen.generate(query)
            
            if not self.validator.validate(cypher):
                return "Query không hợp lệ"

        # =========================
        # EXECUTE
        # =========================
        data = self.db.query(cypher)

        print("\n===== RAW DATA =====")
        print(data)

        # =========================
        # EMPTY CHECK
        # =========================
        if not data:
            return "Không có dữ liệu phù hợp."

        # =========================
        # DEDUP
        # =========================
        def deduplicate(data):
            seen = set()
            result = []

            for d in data:
                key = tuple((k, str(v)) for k, v in d.items())
                if key not in seen:
                    seen.add(key)
                    result.append(d)

            return result

        data = deduplicate(data)

        # =========================
        # SAVE CONTEXT
        # =========================
        self.context.add_context(query, mapped, plan, data)

        # =========================
        # FILTER (TỐI ƯU #4)
        # =========================
        filtered_data = self.filter_data_by_query(query, data, plan)  # ← Thêm plan

        # =========================
        # FAST RULE
        # =========================
        fast = self.fast_answer(query, filtered_data)
        if fast:
            return self.answer_generator.generate(query, [{"answer": fast}], plan=plan)

        # =========================
        # UNIFIED REASON + ANSWER (TỐI ƯU #2 + #5)
        # =========================
        reason = self.reasoner.reason(query, data, plan.get("type"))  # ← Pass plan_type

        if reason:
            print("\n===== RULE RESULT =====")
            print(reason)

            if isinstance(reason, dict):
                if "message" in reason and "data" not in reason:
                    return reason["message"]
                result_data = reason.get("data", reason)
            else:
                result_data = reason
            # Normalise COMPARE outputs: if result_data contains list of string lines,
            # parse them into structured records so AnswerGenerator gets consistent dicts
            if plan.get("type") == "COMPARE":
                # result_data may be {'type':'COMPARE','data':[...]} or a plain list
                candidate = None
                if isinstance(result_data, dict) and isinstance(result_data.get('data'), list):
                    candidate = result_data.get('data')
                elif isinstance(result_data, list):
                    candidate = result_data

                parsed = None
                if candidate and all(isinstance(x, str) for x in candidate):
                    parsed_items = []
                    for s in candidate:
                        r = self.answer_generator._parse_string_record(s)
                        if r:
                            parsed_items.append(r)
                    if parsed_items:
                        parsed = parsed_items

                if parsed:
                    return self.answer_generator.generate(query, parsed, plan=plan)

            return self.answer_generator.generate(query, result_data, plan=plan)

        return self.answer_generator.generate(query, filtered_data, plan=plan)