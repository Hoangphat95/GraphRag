import time


class Metrics:

    def __init__(self):
        self.logs = []

    def start_timer(self):
        return time.time()

    def end_timer(self, start_time):
        return round(time.time() - start_time, 3)

    def log(self, query, cypher, result, latency):

        record = {
            "query": query,
            "cypher": cypher,
            "result_count": len(result) if result else 0,
            "latency": latency
        }

        self.logs.append(record)

        # debug realtime
        print("====== METRICS ======")
        print(record)
        print("=====================")