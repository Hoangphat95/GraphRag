import os
from dotenv import load_dotenv
from google import genai
import time

load_dotenv()


class LLMClient:
    def __init__(self, model_name=None, temperature=0.0, max_retries=2):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("❌ GEMINI_API_KEY not found")

        self.client = genai.Client(api_key=api_key)

        # 🔥 cho phép chọn model linh hoạt
        self.model = model_name or "models/gemini-3.1-flash-lite-preview"

        self.temperature = temperature
        self.max_retries = max_retries

    def chat(self, prompt: str):

        if not prompt or len(prompt.strip()) == 0:
            print("⚠️ Empty prompt → skip LLM")
            return ""

        for attempt in range(self.max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )

                # 🔥 handle trường hợp Gemini trả về None
                if not response or not hasattr(response, "text"):
                    print("⚠️ Empty response from Gemini")
                    return ""

                return response.text.strip()

            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"❌ Gemini error (final):", e)

                # retry nhẹ
                time.sleep(2 * (attempt + 1))

        # ❌ fail toàn bộ
        return ""