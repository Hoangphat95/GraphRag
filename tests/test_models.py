import os
import pytest

# This test calls external API; skip by default unless explicitly enabled.
if os.getenv("RUN_EXTERNAL_TESTS") != "1" or not os.getenv("GEMINI_API_KEY"):
    pytest.skip("Skipping external model listing test; set RUN_EXTERNAL_TESTS=1 and GEMINI_API_KEY to run", allow_module_level=True)

from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("===== AVAILABLE MODELS =====")
try:
    for m in client.models.list():
        print(m.name)
except Exception as e:
    import pytest
    pytest.skip(f"Skipping external models test due to API error: {e}", allow_module_level=True)