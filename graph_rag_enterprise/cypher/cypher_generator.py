import os
from llm.llm_client import LLMClient
from llm.prompt_cypher import build_cypher_prompt
import json


class CypherGenerator:
    def __init__(self):
        self.llm = LLMClient(model_name="models/gemini-3.1-flash-lite-preview")

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(BASE_DIR, "graph_schema.json")

        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

    def generate(self, query: str):
        prompt = build_cypher_prompt(query, self.schema)

        print("\n===== CYPHER PROMPT =====")
        print(prompt)

        cypher = self.llm.chat(prompt)

        print("\n===== RAW LLM CYPHER =====")
        print(cypher)

        if not cypher:
            print("⚠️ LLM trả về rỗng → sẽ fallback")

        # clean
        cypher = cypher.replace("```cypher", "").replace("```", "").strip()

        print("\n===== CLEAN CYPHER =====")
        print(cypher)

        return cypher