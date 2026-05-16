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

        speed = tire.get("toc_do_toi_da") or 0
        load = tire.get("tai_trong_lon_nhat") or 0
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
        # QUERY DATA (🔥 QUAN TRỌNG)
        # ======================
        cypher = """
        MATCH (t:Tire)
        RETURN 
            t.size AS size,
            t.toc_do_toi_da AS toc_do_toi_da,
            t.tai_trong_lon_nhat AS tai_trong_lon_nhat,
            t.duong_kinh_ngoai AS duong_kinh_ngoai,
            t.gia_ban_co_vat AS gia
        LIMIT 50
        """

        data = self.db.query(cypher)

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