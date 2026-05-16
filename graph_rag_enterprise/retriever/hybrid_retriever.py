from mapper.mapper import Mapper
from mapper.embedding_matcher import EmbeddingMatcher

class HybridRetriever:

    def __init__(self):
        self.mapper = Mapper()
        self.embed = EmbeddingMatcher()

    def retrieve(self, query):

        mapped = self.mapper.map(query)
        semantic = self.embed.match(query)

        # =========================
        # MERGE CONTEXT (QUAN TRỌNG)
        # =========================
        enriched = {
            "mapped": mapped,
            "semantic": semantic,
            "has_size": any(m.get("column") == "size" for m in mapped)
        }

        print("\n===== RETRIEVER OUTPUT =====")
        print(enriched)

        return enriched