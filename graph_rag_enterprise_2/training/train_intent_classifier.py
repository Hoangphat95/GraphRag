#!/usr/bin/env python3
"""
training/train_intent_classifier.py  — v2
==========================================
Chạy: python training/train_intent_classifier.py

Thay đổi so với v1:
  - Dùng SentenceTransformer thay BERT (nhanh hơn 10x, nhỏ hơn 7x)
  - Stratified split để đảm bảo mọi class có mẫu test
  - In classification report chi tiết từng class
  - Lưu model vào models/intent_classifier/intent_clf.pkl
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.intent_classifier import IntentClassifier
from sklearn.model_selection import train_test_split
import json


def main():
    print("=" * 55)
    print("  Training Intent Classifier v2")
    print("  Backend: SentenceTransformer + LogisticRegression")
    print("=" * 55)

    clf = IntentClassifier()

    # ── 1. Tạo dataset ──────────────────────────────────────
    print("\n[1/4] Tạo training dataset...")
    df = clf.create_training_data()
    print(f"  Tổng: {len(df)} samples")
    print("\n  Phân bố:")
    dist = df["intent"].value_counts()
    for intent, count in dist.items():
        bar = "█" * (count // 2)
        print(f"    {intent:<15} {count:>3}  {bar}")

    # ── 2. Train / test split (stratified) ─────────────────
    print("\n[2/4] Split 80/20 stratified...")
    train_df, test_df = train_test_split(
        df, test_size=0.2, stratify=df["intent"], random_state=42
    )
    print(f"  Train: {len(train_df)}  |  Test: {len(test_df)}")

    # ── 3. Train ─────────────────────────────────────────────
    print("\n[3/4] Training...")
    clf.build_model(len(df["intent"].unique()))
    clf.train(train_df)

    # ── 4. Evaluate ──────────────────────────────────────────
    print("\n[4/4] Evaluation:")
    report = clf.evaluate(test_df)

    print(f"\n  Overall accuracy: {report['accuracy']:.3f}")
    print(f"\n  {'Intent':<15} {'Precision':>9} {'Recall':>7} {'F1':>6} {'Support':>8}")
    print("  " + "-" * 50)
    for intent in sorted(report.keys()):
        if intent in ("accuracy", "macro avg", "weighted avg"):
            continue
        r = report[intent]
        print(f"  {intent:<15} {r['precision']:>9.2f} {r['recall']:>7.2f} "
              f"{r['f1-score']:>6.2f} {int(r['support']):>8}")
    print("  " + "-" * 50)
    wa = report["weighted avg"]
    print(f"  {'weighted avg':<15} {wa['precision']:>9.2f} {wa['recall']:>7.2f} "
          f"{wa['f1-score']:>6.2f}")

    # ── 5. Save ──────────────────────────────────────────────
    model_path = os.path.join(
        os.path.dirname(__file__), "..", "models", "intent_classifier"
    )
    clf.save_model(model_path)
    print(f"\n  Saved → {model_path}/")

    # ── 6. Smoke test ────────────────────────────────────────
    print("\n  Smoke test:")
    smoke_tests = [
        ("lốp 120/70-17 tốc độ bao nhiêu",          "SPEED"),
        ("so sánh 100/80-14 và 110/80-14",           "COMPARE"),
        ("lốp nào chịu tải tốt nhất",                "MAX_LOAD"),
        ("xe Vision nên dùng lốp gì",                "RECOMMEND"),
        ("lốp 2.50-17 đạt tiêu chuẩn gì",           "MULTI_HOP"),
        ("lốp 120/70-17 bơm bao nhiêu bar",          "PRESSURE"),
        ("giá lốp 2.50-17",                          "PRICE"),
        ("lốp nào tốt nhất",                         "NO_MATCH"),
        ("lốp nào chạy nhanh nhất",                  "MAX_SPEED"),
        ("tư vấn lốp đi đường dài cho Exciter",      "RECOMMEND"),
    ]
    ok = 0
    for query, expected in smoke_tests:
        r    = clf.predict(query)
        hit  = r["intent"] == expected
        flag = "✅" if hit else "❌"
        ok  += int(hit)
        print(f"  {flag} [{expected:<10}] '{query}' → {r['intent']} ({r['confidence']:.2f})")

    print(f"\n  Smoke test: {ok}/{len(smoke_tests)} passed")
    print("\n✅ Training hoàn tất!")


if __name__ == "__main__":
    main()