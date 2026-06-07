import time

def main():
    from pipeline.orchestrator_v3 import GraphRAGv3

    g = GraphRAGv3()

    convo = [
        "Mình muốn mua lốp cho xe máy, kích thước 120/70-17, gợi ý cho mình vài mẫu phù hợp",
        "Cái nào chịu tải cao nhất trong số đó?",
        "So sánh 2 mẫu lốp vừa rồi về tốc độ và giá",
        "Mình ưu tiên tiêu chuẩn chất lượng, giới thiệu những mẫu tốt nhất",
        "Giá của mẫu đầu tiên bao nhiêu (đã VAT)?",
        "Mình muốn mua 2 cái, tổng chi phí là bao nhiêu?",
        "Còn lốp 2.50-17 dùng cho xe tải nhẹ thì sao?",
        "Reset context",
        "Tư vấn cho mình lốp 100/80-14 giá rẻ nhưng vẫn an toàn"
    ]

    for i, q in enumerate(convo, 1):
        if q.lower().startswith('reset'):
            g.reset_context()
            print("[SYSTEM] Context reset")
            continue
        print(f"\n--- TURN {i}: {q}")
        try:
            res = g.run(q)
            print("=> Response:")
            print(res)
        except Exception as e:
            print("ERROR during pipeline run:", e)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
