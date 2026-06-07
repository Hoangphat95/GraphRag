import time
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
from infra import metrics_prometheus as metrics

import unicodedata
import re
try:
    from opentelemetry import trace as ot_trace
except Exception:
    ot_trace = None


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

    def _unpack_build_result(self, build_result):
        if build_result is None:
            return None, None
        if isinstance(build_result, tuple):
            if len(build_result) == 2:
                return build_result
            if len(build_result) == 1:
                return build_result[0], None
        if isinstance(build_result, list):
            if len(build_result) >= 2:
                return build_result[0], build_result[1]
            if len(build_result) == 1:
                return build_result[0], None
        return build_result, None

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
        start = time.time()
        print(f"\n🔍 Query: {query}")

        # start pipeline trace
        span_ctx = None
        if ot_trace is not None:
            tracer = ot_trace.get_tracer(__name__)
            span_ctx = tracer.start_as_current_span('pipeline.run', attributes={'query.length': len(query) if query else 0})
            span_ctx.__enter__()
        
        # =========================
        # RETRIEVE
        # =========================
        r = self.retriever.retrieve(query)
        try:
            # annotate pipeline span with retriever info
            if span_ctx is not None:
                try:
                    span = ot_trace.get_tracer(__name__).get_current_span()
                    if span is not None:
                        span.set_attribute('retriever.uses_faiss', bool(r.get('uses_faiss')))
                except Exception:
                    pass
        except Exception:
            pass
        # record retriever matches
        try:
            mapped = r.get("mapped", [])
            if metrics.retriever_matches is not None:
                # increment by number of mapped items (or 1)
                metrics.retriever_matches.labels(strategy="hybrid").inc(max(1, len(mapped)))
        except Exception:
            pass
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

        # Special-case: MAX_LOAD requests without explicit sizes but with numeric threshold
        if plan.get("type") == "MAX_LOAD" and not plan.get("sizes"):
            # try to parse numeric threshold like '400 kg' or '>400'
            num_match = re.search(r"(?:>|>=)?\s*(\d{2,4})\s*kg", query.lower())
            if not num_match:
                num_match = re.search(r">\s*(\d{2,4})", query.lower())
            if num_match:
                try:
                    min_load = int(num_match.group(1))
                    cy = "MATCH (t:Tire) WHERE coalesce(t.tai_trong_lon_nhat, 0) >= $min RETURN t LIMIT 10"
                    data = self.db.query(cy, params={"min": min_load})
                    if data:
                        data = [d for d in data]
                        # continue pipeline with these results
                        data = normalize_data(data)
                        data = list({tuple(sorted(d.items())): d for d in data}.values())
                        self.context.add_context(query, mapped, plan, data)
                        filtered = self.filter_data_by_query(query, data, plan)
                        fast = self.fast_answer(query, filtered)
                        if fast:
                            return self.answer_generator.generate(query, [{"answer": fast}], plan=plan)
                        reason = self.reasoner.reason(query, data, plan.get("type"))
                        if reason:
                            return self.answer_generator.generate(query, reason if not isinstance(reason, dict) else reason.get("data", reason), plan=plan)
                        return self.answer_generator.generate(query, filtered, plan=plan)
                except Exception:
                    pass

        # =========================
        # ATTRIBUTE SEARCH FALLBACK
        # If planner detected an attribute-oriented query (e.g. "thoát nước", "ít ồn"),
        # try a relaxed DB search across text fields before asking for more info.
        if plan.get("type") == "ATTRIBUTE_SEARCH":
            attr = plan.get("attribute")
            q_attr = plan.get("query") or q
            # map abstract attributes to short search terms likely present in DB
            attr_term_map = {
                "drainage": "thoat nuoc",
                "noise": "it on",
                "durability": "do ben",
                "warranty": "bao hanh",
                "tube": "sam",
                "price": "gia",
                "road_trip": "duong truong",
                "high_load": "400",
                "service": "dich vu",
                "discount": "giam gia",
                "compatibility": "tuong thich"
            }
            search_q = attr_term_map.get(attr, q_attr)
            print(f"\n🔁 ATTRIBUTE_SEARCH fallback for attribute: {attr} → q={q_attr}")
            # If retriever mapped specific columns, try searching those properties first
            fb_data = None
            for mcol in [m.get('column') for m in mapped if m.get('column')]:
                try:
                    col_cypher = f"MATCH (t:Tire) WHERE toLower(toString(coalesce(t.{mcol}, ''))) CONTAINS $q RETURN t LIMIT 10"
                    fb_data = self.db.query(col_cypher, params={"q": search_q})
                except Exception:
                    fb_data = None
                if fb_data:
                    break

            # fallback: broad text match across common text fields and any property values
            if not fb_data:
                fallback_cypher = """
                MATCH (t:Tire)
                     WHERE toLower(toString(coalesce(t.name, ''))) CONTAINS $q
                         OR ANY(k IN keys(t) WHERE toLower(toString(t[k])) CONTAINS $q)
                RETURN t LIMIT 10
                """
                try:
                    fb_data = self.db.query(fallback_cypher, params={"q": search_q})
                except Exception:
                    fb_data = None

            print("\n===== ATTRIBUTE FALLBACK RAW =====")
            print(fb_data)

            # deduplicate helper used by both fallback branches
            def deduplicate_attr(data):
                seen = set()
                result = []
                for d in data:
                    key = tuple((k, str(v)) for k, v in d.items())
                    if key not in seen:
                        seen.add(key)
                        result.append(d)
                return result

            if not fb_data:
                # If no precise matches, return helpful top-N candidates from DB instead of asking for more info
                try:
                    sample = self.db.query("MATCH (t:Tire) RETURN t LIMIT 3", params=None)
                except Exception:
                    sample = None

                if sample:
                    sample = deduplicate_attr(sample)
                    # save context and format a helpful answer summarising candidates
                    self.context.add_context(query, mapped, plan, sample)
                    filtered_sample = self.filter_data_by_query(query, sample, plan)
                    preface = "Mình không tìm thấy bản ghi nêu rõ tiêu chí này, nhưng có một vài mẫu trong hệ thống bạn có thể tham khảo:"
                    # attach preface as first answer entry so AnswerGenerator can format
                    entries = [{"answer": preface}] + filtered_sample
                    return self.answer_generator.generate(query, entries, plan=plan)

                # no sample data either -> fall back to original behavior
                reason = self.reasoner.reason(query, [], plan.get("type"))
                if isinstance(reason, dict) and reason.get("message"):
                    return reason["message"]
                return "Mình cần thêm thông tin để tư vấn chính xác hơn."

            # deduplicate (db returns normalized records already)
            fb_data = deduplicate_attr(fb_data)

            # Save context and continue with normal answer pipeline
            self.context.add_context(query, mapped, plan, fb_data)
            filtered_fb = self.filter_data_by_query(query, fb_data, plan)
            fast_fb = self.fast_answer(query, filtered_fb)
            if fast_fb:
                return self.answer_generator.generate(query, [{"answer": fast_fb}], plan=plan)

            reason_fb = self.reasoner.reason(query, fb_data, plan.get("type"))
            if reason_fb:
                if isinstance(reason_fb, dict):
                    if "message" in reason_fb and "data" not in reason_fb:
                        return reason_fb["message"]
                    result_data = reason_fb.get("data", reason_fb)
                else:
                    result_data = reason_fb
                return self.answer_generator.generate(query, result_data, plan=plan)

            return self.answer_generator.generate(query, filtered_fb, plan=plan)

        # =========================
        # NO_MATCH DIRECT RESPONSE
        # =========================
        if plan.get("type") == "NO_MATCH":
            qn = self._normalize_text(query)
            reason_text = self._normalize_text(plan.get("reason", ""))

            # heavy-load / cargo queries: return the strongest available candidates
            if any(term in qn for term in ["chiu tai", "tai nang", "cho hang", "tai >", ">400"]) or "load signal" in reason_text:
                try:
                    top_loads = self.db.query(
                        "MATCH (t:Tire) WHERE t.tai_trong_lon_nhat IS NOT NULL RETURN t.size AS size, t.brand AS brand, t.tai_trong_lon_nhat AS max_load, t.toc_do_toi_da AS max_speed, t.gia_ban_co_vat AS price ORDER BY t.tai_trong_lon_nhat DESC LIMIT 3"
                    )
                except Exception:
                    top_loads = None
                if top_loads:
                    top_loads = normalize_data(top_loads)
                    return self.answer_generator.generate(
                        query,
                        top_loads,
                        plan={"type": "MAX_LOAD", "sizes": []}
                    )

            # price / filter / discount queries: show available candidates rather than asking back
            if any(term in qn for term in ["giam gia", "khuyen mai", "loc lop", "gia tang dan", "hang x"]) or "price signal" in reason_text:
                try:
                    candidates = self.db.query(
                        "MATCH (t:Tire) WHERE t.gia_ban_co_vat IS NOT NULL RETURN t.size AS size, t.brand AS brand, t.gia_ban_co_vat AS price, t.tai_trong_lon_nhat AS max_load, t.toc_do_toi_da AS max_speed ORDER BY t.gia_ban_co_vat ASC LIMIT 3"
                    )
                except Exception:
                    candidates = None
                if candidates:
                    candidates = normalize_data(candidates)
                    return self.answer_generator.generate(
                        query,
                        candidates,
                        plan={"type": "PRICE", "sizes": []}
                    )

            # service / appointment queries: answer directly with an operational fallback
            if any(term in qn for term in ["dat lich", "phi lap", "lap dat", "dich vu"]):
                return (
                    "Hiện tại hệ thống chưa có dữ liệu đặt lịch hoặc phí lắp cụ thể. "
                    "Tuy nhiên, mình có thể hỗ trợ bạn chọn mẫu lốp phù hợp trước, rồi đối chiếu phí lắp tại cửa hàng khi bạn chốt size và hãng."
                )

            # tube / compatibility / wear / warranty queries: give a direct data-based summary if possible
            if any(term in qn for term in ["sam", "tube", "van", "tuong thich", "bao hanh", "do on"]):
                try:
                    sample = self.db.query("MATCH (t:Tire) RETURN t LIMIT 3")
                except Exception:
                    sample = None
                if sample:
                    sample = normalize_data(sample)
                    return self.answer_generator.generate(
                        query,
                        sample,
                        plan={"type": "SINGLE", "sizes": []}
                    )

            reason = self.reasoner.reason(query, [], plan.get("type"))
            if isinstance(reason, dict) and reason.get("message"):
                return reason["message"]
            return "Mình cần thêm thông tin để tư vấn chính xác hơn."

        # =========================
        # BUILD CYPHER
        # =========================
        build_result = self.builder.build(plan)
        cypher, params = self._unpack_build_result(build_result)

        if cypher is None:
            return "Không thể tạo truy vấn Cypher"

        # =========================
        # VALIDATE + LLM FALLBACK (TỐI ƯU #3)
        # =========================
        valid, reason = self.validator.validate(cypher, params=params)
        if not valid:
            print(f"\n⚠️ Cypher invalid ({reason}) → try LLM fallback")
            gen = CypherGenerator()
            cypher = gen.generate(query)
            params = None

            valid2, reason2 = self.validator.validate(cypher, params=None)
            if not valid2:
                return "Query không hợp lệ"

        # =========================
        # EXECUTE
        # =========================
        data = self.db.query(cypher, params=params)
        try:
            if span_ctx is not None:
                try:
                    span = ot_trace.get_tracer(__name__).get_current_span()
                    if span is not None:
                        span.set_attribute('db.cypher.rows', len(data) if data is not None else 0)
                except Exception:
                    pass
        except Exception:
            pass
        # observe pipeline latency
        try:
            if metrics.pipeline_latency is not None:
                metrics.pipeline_latency.observe(round(time.time() - start, 3))
        except Exception:
            pass

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

        # normalize DB records to canonical keys (max_speed, max_load, price, speed, load)
        data = normalize_data(data)

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

        res = self.answer_generator.generate(query, filtered_data, plan=plan)
        # best-effort span cleanup
        if span_ctx is not None:
            try:
                span_ctx.__exit__(None, None, None)
            except Exception:
                pass
        return res