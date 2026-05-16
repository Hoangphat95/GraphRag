# app/test_mapper.py

from value_mapper import ValueMapper

mapper = ValueMapper()

queries = [

    # 🔥 SIZE + SPEED
    "lốp 18x2.50 có tốc độ tối đa bao nhiêu",
    "lốp 110/70-14 speed max là gì",

    # 🔥 SIZE + LOAD
    "lốp 90/90-17 chịu tải bao nhiêu",
    "tire 100/80-17 max load là bao nhiêu",

    # 🔥 SIZE + PRESSURE
    "lốp 2.75-18 áp suất bao nhiêu",
    "pressure của lốp 110/80-14 là gì",

    # 🔥 SIZE + PATTERN
    "lốp 100/90-17 có kiểu hoa gì",
    "tread pattern của lốp 90/90-14 là gì",

    # 🔥 SIZE + CATEGORY
    "lốp 18x2.50 thuộc nhóm nào",
    "loại lốp của 110/70-14 là gì",

    # 🔥 SIZE + RIM
    "lốp 110/70-14 có đường kính vành là bao nhiêu",
    "rim size của lốp 90/90-17 là gì",

    # 🔥 CHỈ HỎI FIELD (NO SIZE)
    "tốc độ tối đa của lốp là bao nhiêu",
    "áp suất lốp tiêu chuẩn là gì",
    "đường kính vành phổ biến là bao nhiêu",

    # 🔥 MIX LANGUAGE
    "max speed của tire 100/80-17",
    "load capacity của lốp 90/90-14",

    # 🔥 EDGE CASE
    "lốp size 999x999 có gì đặc biệt",
    "random text không liên quan",
]


def run_test():
    for query in queries:
        print("\n==============================")
        print("QUERY:", query)

        results = mapper.map_query(query)

        print("RESULT:")
        if not results:
            print("❌ NO RESULT")
            continue

        for r in results:
            value = r.get("value", "N/A")
            column = r.get("column", "N/A")
            score = r.get("score", 0)
            rtype = r.get("type", "")

            print(f"{r['query_part']} → {value} → {column} ({score:.2f}) [{rtype}]")


if __name__ == "__main__":
    run_test()