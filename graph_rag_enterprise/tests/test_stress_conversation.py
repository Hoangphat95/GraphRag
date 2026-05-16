import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from pipeline.orchestrator_v3 import GraphRAGv3


def test_stress_conversation():
    """Stress-test multi-turn conversation over many turns.

    Default turns = 100. Override with env STRESS_TURNS (50-200).
    The test asserts the system responds without raising exceptions and
    returns string results across the conversation.
    """
    turns = int(os.environ.get("STRESS_TURNS", "100"))
    turns = max(1, min(turns, 200))

    rag = GraphRAGv3()

    queries = [
        "Lốp 120/70-17 giá bao nhiêu?",
        "Lốp 2.50-17 chịu tải được bao nhiêu?",
        "So sánh 100/80-14 và 110/80-14",
        "Trong danh sách này, lốp nào có tốc độ cao nhất?",
        "Lốp 120/70-17 do công ty nào sản xuất?",
        "Mẫu này chịu tải được bao nhiêu?",
        "So sánh 2 lốp trên đi",
        "Lốp nào tốt nhất?",
        "Cho mình biết giá lốp 2.50-17 hiện tại",
    ]

    start = time.time()
    last_result = None
    for i in range(turns):
        q = queries[i % len(queries)]
        # vary phrasing a bit
        if i % 7 == 0:
            q = q + f" (turn {i+1})"

        try:
            res = rag.run(q)
        except Exception as e:
            raise AssertionError(f"Exception at turn {i+1}: {e}")

        assert res is not None
        assert isinstance(res, (str, list, dict))
        last_result = res

        if (i + 1) % 10 == 0:
            dur = time.time() - start
            print(f"Completed {i+1}/{turns} turns (elapsed {dur:.1f}s)")

    assert last_result is not None
