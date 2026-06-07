import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from pipeline.orchestrator_v3 import GraphRAGv3

rag = GraphRAGv3()

# =========================================
# 11 CÂU HỎI COVER TẤT CẢ LUỒNG XỬ LÝ
# =========================================

queries = [
    # 1️⃣ SINGLE + FAST_ANSWER (keyword rõ "tốc độ" + 1 size)
    "Cho mình hỏi lốp 120/70-17 có tốc độ tối đa là bao nhiêu?",
    
    # 2️⃣ SINGLE + SEMANTIC FALLBACK (keyword không rõ nhưng embedding match được "chịu tải")
    "Lốp 2.50-17 này chịu tải được bao nhiêu kg?",
    
    # 3️⃣ COMPARE (2 sizes + keyword "so sánh")
    "So sánh giúp mình lốp 100/80-14 và 110/80-14",
     
    # 4️⃣ MAX_SPEED (keyword "cao nhất" + "tốc độ")
    "Trong danh sách này, lốp nào có tốc độ cao nhất?",
    
    # 5️⃣ MAX_LOAD (keyword "cao nhất" + "tải" → reasoner.reason)
    "Lốp nào chịu tải tốt nhất?",
    
    # 6️⃣ MULTI_HOP Company (size + keyword "công ty")
    "Lốp 120/70-17 do công ty nào sản xuất?",
    
    # 7️⃣ MULTI_HOP QualityStandard (size + keyword "tiêu chuẩn")
    "Lốp 2.50-17 đạt tiêu chuẩn gì?",
    
    # 8️⃣ MULTI_HOP Valve (size + keyword "van")
    "Lốp 120/70-17 nên dùng van gì?",
    
    # 9️⃣ FILTER + PRICE (keyword "giá" → filter_data_by_query)
    "Cho mình biết giá lốp 2.50-17 hiện tại",
    
    # 🔟 SEMANTIC FALLBACK + CONTEXT (dùng ngữ cảnh từ câu trước)
    "Mẫu này chịu tải được bao nhiêu?",
    
    # 1️⃣1️⃣ NO_MATCH (không có size, không có keyword rõ)
    "Lốp nào tốt nhất?",
    
    # 1️⃣2️⃣ CONTEXTUAL COMPARE (so sánh last two tires)
    "Lốp 2.50-17 và 110/70-14 giá bao nhiêu?",
    "So sánh 2 lốp trên đi",
]

# =========================================
# DETAIL MỖI LUỒNG
# =========================================
test_cases = [
    ("SINGLE + FAST_ANSWER", queries[0]),
    ("SINGLE + SEMANTIC", queries[1]),
    ("COMPARE", queries[2]),
    ("MAX_SPEED", queries[3]),
    ("MAX_LOAD", queries[4]),
    ("MULTI_HOP (Company)", queries[5]),
    ("MULTI_HOP (QualityStandard)", queries[6]),
    ("MULTI_HOP (Valve)", queries[7]),
    ("FILTER + PRICE", queries[8]),
    ("SEMANTIC FALLBACK + CONTEXT", queries[9]),
    ("NO_MATCH", queries[10]),
    ("CONTEXTUAL COMPARE", queries[11]),
    ("CONTEXTUAL COMPARE FOLLOW-UP", queries[12]),
]

print("\n" + "="*70)
print("📊 TEST COVER TẤT CẢ LUỒNG XỬ LÝ CỦA ORCHESTRATOR_V3")
print("="*70)

for i, (case_name, query) in enumerate(test_cases, 1):
    print(f"\n{'='*70}")
    print(f"Test {i:2d}: {case_name}")
    print(f"Query: {query}")
    print(f"{'='*70}")
    
    try:
        result = rag.run(query)
        print(f"\n✅ Result:\n{result}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

print(f"\n{'='*70}")
print("✅ TEST HOÀN THÀNH!")
print(f"{'='*70}")