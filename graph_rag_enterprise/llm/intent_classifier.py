import torch
import torch.nn as nn
from transformers import BertTokenizer, BertModel
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import json
import os
from typing import List, Dict, Tuple

class IntentClassifier:
    """
    ML Model để phân loại intent của query
    Sử dụng BERT fine-tuned cho task classification
    """

    def __init__(self, model_path: str = None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')
        self.model = None
        self.label_encoder = None

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def create_training_data(self) -> pd.DataFrame:
        """Tạo dataset training từ các queries mẫu"""

        # Intent types
        intents = {
            'SINGLE': [
                "lốp 120/70-17 tốc độ bao nhiêu",
                "lốp 2.50-17 chịu tải bao nhiêu",
                "lốp 100/90-18 áp suất là gì",
                "đường kính lốp 110/90-18",
                "lốp 120/70-17 giá bao nhiêu",
                "lốp 2.50-17 của hãng nào",
                "lốp 100/90-18 đạt tiêu chuẩn gì"
            ],
            'COMPARE': [
                "so sánh lốp 100/90-18 và 110/90-18",
                "lốp 120/70-17 với 130/70-17 khác nhau thế nào",
                "đối chiếu lốp A và B",
                "lốp 2.50-17 so với 2.75-17"
            ],
            'MAX_SPEED': [
                "lốp nào tốc độ cao nhất",
                "lốp chạy nhanh nhất",
                "tốc độ tối đa cao nhất",
                "lốp có vận tốc max"
            ],
            'MAX_LOAD': [
                "lốp nào chịu tải cao nhất",
                "lốp tải trọng lớn nhất",
                "chịu lực cao nhất",
                "lốp chịu được nhiều nhất"
            ],
            'PRICE': [
                "giá lốp 120/70-17",
                "lốp 2.50-17 bao nhiêu tiền",
                "giá bán lốp 100/90-18",
                "lốp 110/90-18 giá cả"
            ],
            'MULTI_HOP': [
                "lốp 120/70-17 của công ty nào",
                "lốp 2.50-17 đạt tiêu chuẩn gì",
                "lốp 100/90-18 dùng van gì",
                "công ty sản xuất lốp 110/90-18",
                "tiêu chuẩn chất lượng lốp 120/70-17"
            ],
            'NO_MATCH': [
                "lốp nào tốt nhất",
                "mẫu này là gì",
                "lốp này như thế nào",
                "tư vấn lốp xe",
                "lốp phù hợp nhất"
            ]
        }

        # Flatten thành DataFrame
        data = []
        for intent, queries in intents.items():
            for query in queries:
                data.append({'query': query, 'intent': intent})

        df = pd.DataFrame(data)

        # Augment data bằng paraphrasing
        augmented = []
        for _, row in df.iterrows():
            # Thêm variations
            variations = self._generate_variations(row['query'])
            for var in variations:
                augmented.append({'query': var, 'intent': row['intent']})

        augmented_df = pd.DataFrame(augmented)
        final_df = pd.concat([df, augmented_df], ignore_index=True)

        return final_df.drop_duplicates()

    def _generate_variations(self, query: str) -> List[str]:
        """Tạo variations của query để augment data"""

        variations = []

        # Basic paraphrasing rules
        replacements = {
            'lốp': ['lốp xe', 'mâm lốp', 'săm lốp'],
            'tốc độ': ['vận tốc', 'chạy nhanh', 'km/h'],
            'chịu tải': ['tải trọng', 'chở nặng', 'kg'],
            'áp suất': ['sức ép', 'PSI', 'bar'],
            'giá': ['giá bán', 'tiền', 'VND'],
            'so sánh': ['đối chiếu', 'so với', 'thấy sao'],
            'cao nhất': ['tối đa', 'nhiều nhất', 'max'],
            'bao nhiêu': ['là gì', 'thế nào', 'ra sao']
        }

        for old, news in replacements.items():
            if old in query:
                for new in news:
                    variations.append(query.replace(old, new))

        return variations[:3]  # Limit to 3 variations

    def build_model(self, num_labels: int):
        """Build BERT classification model"""

        class BertClassifier(nn.Module):
            def __init__(self, num_labels):
                super(BertClassifier, self).__init__()
                self.bert = BertModel.from_pretrained('bert-base-multilingual-cased')
                self.dropout = nn.Dropout(0.1)
                self.classifier = nn.Linear(self.bert.config.hidden_size, num_labels)

            def forward(self, input_ids, attention_mask):
                outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
                pooled_output = outputs.pooler_output
                pooled_output = self.dropout(pooled_output)
                logits = self.classifier(pooled_output)
                return logits

        self.model = BertClassifier(num_labels).to(self.device)

    def train(self, train_data: pd.DataFrame, epochs: int = 5, batch_size: int = 16):
        """Train the model"""

        # Encode labels
        from sklearn.preprocessing import LabelEncoder
        self.label_encoder = LabelEncoder()
        train_data['label'] = self.label_encoder.fit_transform(train_data['intent'])

        # Prepare data
        train_texts = train_data['query'].tolist()
        train_labels = train_data['label'].tolist()

        # Tokenize
        encodings = self.tokenizer(train_texts, truncation=True, padding=True, max_length=128)

        # Create dataset
        dataset = torch.utils.data.TensorDataset(
            torch.tensor(encodings['input_ids']),
            torch.tensor(encodings['attention_mask']),
            torch.tensor(train_labels)
        )

        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

        # Optimizer
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=2e-5)
        loss_fn = nn.CrossEntropyLoss()

        self.model.train()
        for epoch in range(epochs):
            total_loss = 0
            for batch in dataloader:
                input_ids, attention_mask, labels = [b.to(self.device) for b in batch]

                optimizer.zero_grad()
                outputs = self.model(input_ids, attention_mask)
                loss = loss_fn(outputs, labels)
                loss.backward()
                optimizer.step()

                total_loss += loss.item()

            print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(dataloader):.4f}")

    def predict(self, query: str) -> Dict:
        """Predict intent của query"""

        if self.model is None:
            return {'intent': 'UNKNOWN', 'confidence': 0.0}

        self.model.eval()
        with torch.no_grad():
            encoding = self.tokenizer(query, truncation=True, padding=True, max_length=128, return_tensors='pt')
            input_ids = encoding['input_ids'].to(self.device)
            attention_mask = encoding['attention_mask'].to(self.device)

            outputs = self.model(input_ids, attention_mask)
            probabilities = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probabilities, dim=1)

            intent = self.label_encoder.inverse_transform([predicted.item()])[0]

            return {
                'intent': intent,
                'confidence': confidence.item(),
                'probabilities': probabilities.cpu().numpy().tolist()
            }

    def save_model(self, path: str):
        """Save model và label encoder"""

        os.makedirs(path, exist_ok=True)

        # Save model
        torch.save(self.model.state_dict(), os.path.join(path, 'model.pt'))

        # Save label encoder
        with open(os.path.join(path, 'label_encoder.json'), 'w', encoding='utf-8') as f:
            json.dump({
                'classes': list(self.label_encoder.classes_)
            }, f, ensure_ascii=False, indent=2)

        # Save tokenizer
        self.tokenizer.save_pretrained(path)

    def load_model(self, path: str):
        """Load model và label encoder"""

        # Load label encoder
        with open(os.path.join(path, 'label_encoder.json'), 'r', encoding='utf-8') as f:
            encoder_data = json.load(f)
            from sklearn.preprocessing import LabelEncoder
            import numpy as np
            self.label_encoder = LabelEncoder()
            self.label_encoder.classes_ = np.array(encoder_data['classes'])

        # Build model
        num_labels = len(self.label_encoder.classes_)
        self.build_model(num_labels)

        # Load weights
        model_path = os.path.join(path, 'model.pt')
        self.model.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=True))
        self.model.eval()

    def evaluate(self, test_data: pd.DataFrame) -> Dict:
        """Evaluate model performance"""

        predictions = []
        true_labels = []

        for _, row in test_data.iterrows():
            pred = self.predict(row['query'])
            predictions.append(pred['intent'])
            true_labels.append(row['intent'])

        return classification_report(true_labels, predictions, output_dict=True)

# Usage example
if __name__ == "__main__":
    classifier = IntentClassifier()

    # Create training data
    train_df = classifier.create_training_data()
    print(f"Training data size: {len(train_df)}")

    # Split data
    train_data, test_data = train_test_split(train_df, test_size=0.2, random_state=42)

    # Build and train model
    num_labels = len(train_df['intent'].unique())
    classifier.build_model(num_labels)
    classifier.train(train_data)

    # Evaluate
    eval_results = classifier.evaluate(test_data)
    print("Evaluation Results:")
    print(json.dumps(eval_results, indent=2))

    # Save model
    classifier.save_model('models/intent_classifier')

    # Test prediction
    test_query = "lốp nào chạy nhanh nhất"
    result = classifier.predict(test_query)
    print(f"Query: {test_query}")
    print(f"Predicted intent: {result['intent']} (confidence: {result['confidence']:.2f})")