# app/value_store.py

import pandas as pd
from embeddings import embed_text

EXCEL_FILE = r"E:\KG\Data_mp_final.xlsx"

TARGET_SHEETS = [
    "LOP_XM_DRC",
    "LOP_XM_DPLUS",
    "LOP_XD_DRC",
    "tire_variant",
    "variant_quality_standard"
]


def normalize_text(text: str):
    return text.lower().strip().replace(" ", "")


class ValueStore:
    def __init__(self):
        self.data = []
        self.columns = []

    def build(self):
        sheets = pd.read_excel(EXCEL_FILE, sheet_name=TARGET_SHEETS)

        COLUMN_SYNONYMS = {
            "Tốc độ tối đa": "max speed speed velocity",
            "Chỉ số tải & tốc độ": "load capacity max load tải trọng",
            "Nội áp tiêu chuẩn": "pressure psi kpa áp suất",
            "Kiểu hoa": "pattern tread kiểu hoa",
            "Nhóm lốp": "type category nhóm lốp",
            "Đường kính vành": "rim size rim diameter đường kính vành"
        }

        for sheet_name, df in sheets.items():
            for col in df.columns:

                if "unnamed" in col.lower():
                    continue

                # 🔥 COLUMN EMBEDDING
                extra = COLUMN_SYNONYMS.get(col, "")
                col_text = f"{col} {extra}"
                col_embedding = embed_text(col_text)

                self.columns.append({
                    "column": col,
                    "sheet": sheet_name,
                    "embedding": col_embedding
                })

                # 🔥 VALUE
                unique_values = df[col].dropna().unique()

                for val in unique_values:
                    raw_val = str(val)
                    norm_val = normalize_text(raw_val)

                    if not norm_val:
                        continue

                    text = f"{col}: {raw_val}"
                    embedding = embed_text(text)

                    self.data.append({
                        "value": norm_val,   # 🔥 normalized
                        "raw_value": raw_val,  # 🔥 giữ original để trả ra
                        "column": col,
                        "sheet": sheet_name,
                        "embedding": embedding
                    })

        print(f"Loaded {len(self.data)} values")
        print(f"Loaded {len(self.columns)} columns")


if __name__ == "__main__":
    store = ValueStore()
    store.build()

    print("\n=== SAMPLE DATA ===")
    for item in store.data[:5]:
        print(f"{item['raw_value']} → {item['column']}")