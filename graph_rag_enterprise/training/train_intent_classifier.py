#!/usr/bin/env python3
"""
Script để train Intent Classifier model
Chạy: python train_intent_classifier.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.intent_classifier import IntentClassifier
import json

def main():
    print("🚀 Training Intent Classifier...")

    # Initialize classifier
    classifier = IntentClassifier()

    # Create training data
    print("📊 Creating training dataset...")
    train_df = classifier.create_training_data()
    print(f"✅ Created {len(train_df)} training samples")

    # Show class distribution
    print("\n📈 Class distribution:")
    print(train_df['intent'].value_counts())

    # Build model
    num_labels = len(train_df['intent'].unique())
    print(f"\n🏗️ Building model with {num_labels} classes...")
    classifier.build_model(num_labels)

    # Train model
    print("🎯 Training model...")
    classifier.train(train_df, epochs=10, batch_size=8)

    # Save model
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'intent_classifier')
    print(f"💾 Saving model to {model_path}...")
    classifier.save_model(model_path)

    # Test model
    print("\n🧪 Testing model...")
    test_queries = [
        "lốp 120/70-17 tốc độ bao nhiêu",
        "so sánh lốp A và B",
        "lốp nào chạy nhanh nhất",
        "giá lốp 2.50-17",
        "lốp nào tốt nhất"
    ]

    for query in test_queries:
        result = classifier.predict(query)
        print(f"Query: '{query}' → {result['intent']} ({result['confidence']:.2f})")

    print("\n✅ Training completed! Model saved and ready to use.")

if __name__ == "__main__":
    main()