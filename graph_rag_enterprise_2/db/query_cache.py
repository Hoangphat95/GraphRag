# # db/query_cache.py
# import hashlib

# class QueryCache:
#     def __init__(self):
#         self.cache = {}

#     def get(self, query):
#         return self.cache.get(hash(query))

#     def set(self, query, result):
#         self.cache[hash(query)] = result