from cypher.value_mapper import ValueMapper as CypherValueMapper

class Mapper:

    def __init__(self):
        self.value_mapper = CypherValueMapper()

    def map(self, query: str):

        results = self.value_mapper.map_query(query)

        print("\n===== MAPPED =====")
        print(results)

        return results