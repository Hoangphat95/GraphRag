#!/usr/bin/env python3
"""
Demo: Graph RAG with ML Intent Classification
Hiển thị sự khác biệt giữa rule-based và ML-based intent detection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.intent_classifier import IntentClassifier

def demo_ml_intent():
    print("🚀 Graph RAG Enterprise - ML Intent Classification Demo")
    print("=" * 60)

    # Load ML model
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'models', 'intent_classifier'))
    classifier = IntentClassifier(model_path)

    # Check if model loaded successfully
    if classifier.model is None:
        print("❌ Failed to load ML model. Please train the model first.")
        print("Run: python training/train_intent_classifier.py")
        return

    # Test queries showcasing ML power
    demo_queries = [
        # Standard queries
        ("lốp 120/70-17 tốc độ bao nhiêu", "SINGLE"),
        ("so sánh lốp A và B", "COMPARE"),
        ("lốp nào chạy nhanh nhất", "MAX_SPEED"),

        # Ambiguous queries that ML handles better
        ("cái này nhanh không", "NO_MATCH"),  # ML detects ambiguity
        ("lốp tốt nhất hiện nay", "NO_MATCH"),  # ML understands "tốt nhất"
        ("giá cả lốp xe như thế nào", "PRICE"),  # ML understands "giá cả"

        # Complex natural language
        ("tôi muốn biết lốp 2.50-17 có bền không", "SINGLE"),  # ML understands context
        ("công ty nào sản xuất lốp 100/90-18 vậy", "MULTI_HOP"),  # ML detects company intent
        ("lốp 110/90-18 đạt chuẩn chất lượng gì", "MULTI_HOP"),  # ML understands standards
    ]

    print("🤖 ML Intent Classification Results:")
    print("-" * 60)

    correct = 0
    total = len(demo_queries)

    for query, expected in demo_queries:
        result = classifier.predict(query)
        predicted = result['intent']
        confidence = result['confidence']

        status = "✅" if predicted == expected else "❌"
        if predicted == expected:
            correct += 1

        print(f"{status} '{query}'")
        print(f"   → Predicted: {predicted} ({confidence:.2f}) | Expected: {expected}")
        print()

    accuracy = correct / total * 100
    print(f"🎯 ML Model Accuracy: {correct}/{total} = {accuracy:.1f}%")
    print()

    print("💡 Key Advantages of ML Intent Classification:")
    print("   • Hiểu ngữ nghĩa tự nhiên hơn rule-based")
    print("   • Xử lý queries mơ hồ, không rõ ràng")
    print("   • Học từ data, cải thiện theo thời gian")
    print("   • Robust với variations trong ngôn ngữ")
    print()

    print("🔄 Next Steps to Make 'Mạnh Như Graph RAG Chuyên Nghiệp':")
    print("   1. ✅ Intent Classification (DONE)")
    print("   2. 🔄 Advanced Semantic Retrieval (Neo4j vector index)")
    print("   3. 🔄 Multi-turn Conversation (Context management)")
    print("   4. 🔄 Performance Optimization (Caching, async)")
    print("   5. 🔄 Error Handling & Monitoring")
    print("   6. 🔄 Evaluation Framework")

if __name__ == "__main__":
    demo_ml_intent()