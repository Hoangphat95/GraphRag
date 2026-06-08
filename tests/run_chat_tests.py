#!/usr/bin/env python3
import os
import sys
import traceback
import json

# Ensure project root is on path
HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

try:
    from pipeline.orchestrator_v3 import GraphRAGv3
except Exception:
    GraphRAGv3 = None

QUESTIONS = [
    "Lốp DPLUS 3.00-18 có giá bán có VAT bao nhiêu?",
    "Lốp DPLUS 3.00-18 có tải trọng lớn nhất bao nhiêu kg?",
    "Lốp DPLUS 3.00-18 có tốc độ tối đa bao nhiêu km/h?",
    "Áp suất bơm của lốp DPLUS 3.00-18 là bao nhiêu kPa?",
    "Lốp DPLUS 3.00-18 có kiểu hoa nào?",
    "Lốp DPLUS 3.00-18 có tiêu chuẩn chất lượng nào trong bảng variant_quality_standard?",
    "Lốp DPLUS 110/70-14 có tải trọng lớn nhất bao nhiêu kg?",
    "Lốp DPLUS 110/70-14 có tốc độ tối đa bao nhiêu km/h?",
    "Lốp DPLUS 110/70-14 có những kiểu hoa nào?",
    "Lốp DPLUS 140/70-14 có tải trọng lớn nhất bao nhiêu kg?",
    "Áp suất bơm của lốp DPLUS 140/70-14 là bao nhiêu kPa?",
    "Lốp DPLUS 140/70-14 có những kiểu hoa nào?",
    "Lốp DPLUS 130/70-17 có kiểu hoa nào?",
    "Lốp DPLUS 130/70-17 có tải trọng lớn nhất bao nhiêu kg?",
    "Lốp DPLUS 120/70-17 có đường kính vành bao nhiêu inch?",
    "Lốp DPLUS 120/70-17 có rộng vành thích hợp là gì?",
    "Lốp DPLUS 100/70-17 có kiểu hoa nào?",
    "Lốp DPLUS 90/80-17 có kiểu hoa nào?",
    "Lốp DPLUS nào có tải trọng lớn nhất trong bảng?",
    "Lốp DPLUS nào có tốc độ tối đa 150 km/h?",
    "Lốp DPLUS 100/80-14 có những kiểu hoa nào?",
    "Lốp DPLUS 80/90-17 có những kiểu hoa nào?",
    "Lốp DPLUS 110/90-16 có kiểu hoa nào?",
    "Lốp DPLUS 130/70-12 có những kiểu hoa nào?",
    "Lốp DPLUS 100/90-10 có những kiểu hoa nào?"
]

OUT_MD = os.path.join(HERE, "chat_test_results.md")

def write_result(results):
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("# Kết quả kiểm thử chatbot\n\n")
        for i, item in enumerate(results, 1):
            f.write(f"## Câu {i}: {item['question']}\n\n")
            f.write("**Response:**\n\n")
            if item.get('error'):
                f.write("```")
                f.write(item['error'])
                f.write("```\n\n")
            else:
                resp = item.get('response')
                if isinstance(resp, (dict, list)):
                    f.write('```json\n')
                    f.write(json.dumps(resp, ensure_ascii=False, indent=2))
                    f.write('\n```\n\n')
                else:
                    f.write(str(resp) + "\n\n")

def main():
    results = []

    if GraphRAGv3 is None:
        for q in QUESTIONS:
            results.append({"question": q, "response": None, "error": "GraphRAGv3 class could not be imported."})
        write_result(results)
        print("GraphRAGv3 not available; wrote placeholder results to", OUT_MD)
        return

    try:
        bot = GraphRAGv3()
    except Exception:
        tb = traceback.format_exc()
        for q in QUESTIONS:
            results.append({"question": q, "response": None, "error": f"Failed to instantiate GraphRAGv3:\n{tb}"})
        write_result(results)
        print("Failed to instantiate GraphRAGv3; wrote errors to", OUT_MD)
        return

    for q in QUESTIONS:
        try:
            resp = bot.run(q)
            results.append({"question": q, "response": resp, "error": None})
        except Exception:
            results.append({"question": q, "response": None, "error": traceback.format_exc()})

    write_result(results)
    print("Wrote results to", OUT_MD)

if __name__ == '__main__':
    main()
