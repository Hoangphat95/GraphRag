import unicodedata


class PropertyNormalizer:

    def __init__(self, properties: dict):

        self.raw_to_clean = {}
        self.clean_to_raw = {}
        self.synonyms = {}

        for node, props in properties.items():
            for p in props:
                clean = self.normalize(p)

                self.raw_to_clean[p] = clean
                self.clean_to_raw[clean] = p

        # default synonyms (cleaned form -> canonical raw property)
        # extend this map as needed for local language/synonyms
        default_synonyms = {
            "toc_do": "toc_do_toi_da",
            "toc_do_toi_da": "toc_do_toi_da",
            "toc_do_toi_da_max": "toc_do_toi_da",
            "toc_do_toi_da_toi_da": "toc_do_toi_da",
            "rim": "duong_kinh_vanh",
            "vanh": "duong_kinh_vanh",
            "duong_kinh_vanh": "duong_kinh_vanh",
            "duong_kinh_ngoai": "duong_kinh_ngoai",
            "ngoai": "duong_kinh_ngoai",
            "tai_trong": "tai_trong_lon_nhat",
            "tai_trong_lon_nhat": "tai_trong_lon_nhat",
            "ap_suat": "noi_ap_tieu_chuan",
            "ap_suat_tieu_chuan": "noi_ap_tieu_chuan",
            "gia": "gia_ban_co_vat",
            "gia_ban": "gia_ban_co_vat",
            "pattern": "kieu_hoa",
            "hoa": "kieu_hoa",
        }
        # allow external synonyms.json to extend/override defaults
        try:
            import os, json
            base = os.path.dirname(__file__)
            syn_path = os.path.join(base, "synonyms.json")
            if os.path.exists(syn_path):
                with open(syn_path, "r", encoding="utf-8") as sf:
                    external = json.load(sf)
                    # external should be mapping cleaned -> canonical
                    default_synonyms.update(external)
        except Exception:
            pass

        # keep only synonyms that map to an existing property (raw_to_clean keys)
        for k, v in default_synonyms.items():
            if v in self.raw_to_clean:
                self.synonyms[k] = v

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
        if not detected_column:
            return None

        # if it's already a cleaned key mapping
        if detected_column in self.clean_to_raw:
            return self.clean_to_raw.get(detected_column)

        # try normalize and lookup
        cleaned = self.normalize(detected_column)

        if cleaned in self.clean_to_raw:
            return self.clean_to_raw.get(cleaned)

        # try synonyms
        if cleaned in self.synonyms:
            return self.synonyms.get(cleaned)

        return None