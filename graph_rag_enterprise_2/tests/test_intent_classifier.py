#!/usr/bin/env python3
"""
Test Intent Classifier integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.intent_classifier import IntentClassifier

def test_intent_classifier():
    print("🧪 Testing Intent Classifier...")

    # Load model
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'intent_classifier')
    if not os.path.exists(model_path):
        print("❌ Model not found. Please train the model first.")
        return

    classifier = IntentClassifier(model_path)

    # Test queries
    test_queries = [
        "lốp 120/70-17 tốc độ bao nhiêu",
        "so sánh lốp A và B",
        "lốp nào chạy nhanh nhất",
        "giá lốp 2.50-17",
        "lốp nào tốt nhất",
        "lốp 100/90-18 của công ty nào",
        "lốp 2.50-17 đạt tiêu chuẩn gì"
    ]

    print("\n📊 Test Results:")
    print("-" * 50)

    for query in test_queries:
        result = classifier.predict(query)
        status = "✅" if result['confidence'] > 0.8 else "⚠️"
        print(f"{status} '{query}' → {result['intent']} ({result['confidence']:.2f})")

    print("\n✅ Intent Classifier test completed!")

if __name__ == "__main__":
    test_intent_classifier()