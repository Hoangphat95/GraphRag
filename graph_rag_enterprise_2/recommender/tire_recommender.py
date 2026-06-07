from db.neo4j_client import Neo4jClient
from recommender.context_parser import ContextParser
from recommender.scoring_engine import ScoringEngine
from recommender.explanation_generator import ExplanationGenerator

class SmartRecommender:

    def __init__(self, db, answer_llm):
        self.db = db
        self.answer_llm = answer_llm

    # =========================
    # SCORING FUNCTION
    # =========================
    def score_tire(self, tire, mode="long_trip"):

        score = 0

        speed = tire.get("max_speed") or tire.get("toc_do_toi_da") or tire.get("speed") or 0
        load = tire.get("max_load") or tire.get("tai_trong_lon_nhat") or tire.get("load") or 0
        diameter = tire.get("duong_kinh_ngoai") or 0

        if mode == "long_trip":
            score += speed * 0.5
            score += load * 0.4
            score += diameter * 0.1

        elif mode == "city":
            score += (150 - speed) * 0.4   # tốc độ thấp → dễ điều khiển
            score += load * 0.3
            score += (600 - diameter) * 0.3

        return score

    # =========================
    # MAIN RECOMMEND
    # =========================
    def recommend(self, query: str):

        q = query.lower()

        # ======================
        # DETECT MODE
        # ======================
        if any(k in q for k in ["đường dài", "đi xa"]):
            mode = "long_trip"
        elif any(k in q for k in ["đi phố", "trong phố"]):
            mode = "city"
        else:
            mode = "general"

        # ======================
        # QUERY DATA (moved scoring into Cypher to reduce bandwidth)
        # ======================
        limit = 50

        if mode == "long_trip":
            score_expr = (
                "(coalesce(t.toc_do_toi_da,0)*0.5 + coalesce(t.tai_trong_lon_nhat,0)*0.4 + coalesce(t.duong_kinh_ngoai,0)*0.1)"
            )
        elif mode == "city":
            score_expr = (
                "((150 - coalesce(t.toc_do_toi_da,0))*0.4 + coalesce(t.tai_trong_lon_nhat,0)*0.3 + (600 - coalesce(t.duong_kinh_ngoai,0))*0.3)"
            )
        else:
            score_expr = (
                "(coalesce(t.toc_do_toi_da,0)*0.33 + coalesce(t.tai_trong_lon_nhat,0)*0.33 + coalesce(t.duong_kinh_ngoai,0)*0.34)"
            )

        cypher = f"""
        MATCH (t:Tire)
        WITH t, {score_expr} AS score
        RETURN 
            t.size AS size,
            t.toc_do_toi_da AS toc_do_toi_da,
            t.tai_trong_lon_nhat AS tai_trong_lon_nhat,
            t.duong_kinh_ngoai AS duong_kinh_ngoai,
            t.gia_ban_co_vat AS gia
        ORDER BY score DESC
        LIMIT $limit
        """

        data = self.db.query(cypher, params={"limit": limit})

        if not data:
            return "Không có dữ liệu để tư vấn."

        # ======================
        # SCORE + RANK
        # ======================
        scored = []
        for t in data:
            s = self.score_tire(t, mode)
            t["score"] = s
            scored.append(t)

        scored = sorted(scored, key=lambda x: x["score"], reverse=True)

        top_k = scored[:3]

        # ======================
        # LLM REASONING
        # ======================
        return self.answer_llm.generate_recommendation(query, top_k)