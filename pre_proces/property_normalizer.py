import unicodedata


class PropertyNormalizer:

    def __init__(self, properties: dict):

        self.raw_to_clean = {}
        self.clean_to_raw = {}

        for node, props in properties.items():
            for p in props:
                clean = self.normalize(p)

                self.raw_to_clean[p] = clean
                self.clean_to_raw[clean] = p

    # remove accent + normalize
    def normalize(self, text: str):
        import unicodedata

        text = text.lower()

        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')

        text = text.replace("đ", "d")
        text = text.replace(" ", "_")

        return text

    def get_real_property(self, detected_column: str):
        return self.clean_to_raw.get(detected_column, None)