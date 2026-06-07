import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from llm.answer_generator import AnswerGenerator


def test_format_compare_returns_markdown():
    ag = AnswerGenerator()
    data = [
        {"size": "100/80-14", "brand": "DPLUS", "load": 180.0, "speed": 150.0, "price": 120000},
        {"size": "110/80-14", "brand": "DPLUS", "load": 206.0, "speed": 150.0, "price": 130000},
    ]

    res = ag._format_compare(data)

    assert isinstance(res, str)
    # Should contain table-like markdown or header keywords
    assert "Thuộc tính" in res or "So sánh" in res or "|" in res
