import math
import re
import pandas as pd
from neo4j import GraphDatabase

# ══════════════════════════════════════════════════════════════════════════════
#  CẤU HÌNH  —  chỉnh URI / credentials / đường dẫn file nếu cần
# ══════════════════════════════════════════════════════════════════════════════
NEO4J_URI      = "neo4j://127.0.0.1:7687"
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "tiredrc2026"
EXCEL_FILE     = "E:\KG\Data_mp_final.xlsx"


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _is_nan(v) -> bool:
    """Kiểm tra NaN/None an toàn cho mọi kiểu dữ liệu."""
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    return False


def clean(value) -> str | None:
    """
    Chuẩn hoá một giá trị thành str.strip() hoặc None nếu rỗng/NaN.
    - float nguyên (6.0) → '6'
    - float thập phân (1.4) → '1.4'
    - bool → giữ nguyên bool (xử lý bởi clean_bool)
    """
    if _is_nan(value):
        return None
    if isinstance(value, bool):
        return value  # để clean_bool xử lý
    if isinstance(value, float):
        # 6.0 → '6', 1.85 → '1.85'
        text = str(int(value)) if value == int(value) else str(value)
    else:
        text = str(value)
    text = text.strip()
    return None if text in ("", "nan", "none", "NaN", "None") else text


def clean_bool(value) -> bool | None:
    """Trả về True / False / None."""
    if _is_nan(value):
        return None
    if isinstance(value, (bool, int)):
        return bool(value)
    s = str(value).strip().lower()
    if s in ("true", "1", "có", "yes"):
        return True
    if s in ("false", "0", "không", "no"):
        return False
    return None


def clean_num(value) -> float | None:
    """Trả về float hoặc None."""
    if _is_nan(value):
        return None
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def clean_pattern(value) -> str | None:
    """
    Chuẩn hoá kiểu hoa: int 301 → '301', str 'D354 ' → 'D354'.
    Đảm bảo nhất quán giữa các sheet (tránh tạo node trùng).
    """
    if _is_nan(value):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return None
        value = int(value)
    return str(value).strip()


def parse_size(value) -> str | None:
    """Chuẩn hoá chuỗi kích thước lốp/săm."""
    s = clean(value)
    if not s:
        return None
    # Thay khoảng trắng thừa bằng dấu '-'
    s = re.sub(r"\s+", "-", s)
    return s


# ══════════════════════════════════════════════════════════════════════════════
#  NEO4J CLIENT
# ══════════════════════════════════════════════════════════════════════════════

class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

    def run(self, cypher: str, params: dict | None = None) -> list[dict]:
        with self.driver.session() as s:
            return [r.data() for r in s.run(cypher, params or {})]

    def close(self):
        self.driver.close()


# ══════════════════════════════════════════════════════════════════════════════
#  SCHEMA  (constraints + indexes)
# ══════════════════════════════════════════════════════════════════════════════

_SCHEMA_STATEMENTS = [
    # Constraints
    "CREATE CONSTRAINT tire_unique         IF NOT EXISTS FOR (t:Tire)            REQUIRE (t.size, t.brand)              IS UNIQUE",
    "CREATE CONSTRAINT pattern_unique      IF NOT EXISTS FOR (p:TirePattern)     REQUIRE p.pattern                      IS UNIQUE",
    "CREATE CONSTRAINT quality_unique      IF NOT EXISTS FOR (q:QualityStandard) REQUIRE q.name                         IS UNIQUE",
    "CREATE CONSTRAINT tire_type_unique    IF NOT EXISTS FOR (tt:TireType)       REQUIRE tt.name                        IS UNIQUE",
    "CREATE CONSTRAINT tube_unique         IF NOT EXISTS FOR (tb:Tube)           REQUIRE (tb.size, tb.vehicle_type)     IS UNIQUE",
    "CREATE CONSTRAINT brand_unique        IF NOT EXISTS FOR (b:Brand)           REQUIRE b.name                         IS UNIQUE",
    "CREATE CONSTRAINT van_unique          IF NOT EXISTS FOR (v:Van)             REQUIRE v.name                         IS UNIQUE",
    # Indexes
    "CREATE INDEX tire_vehicle_type        IF NOT EXISTS FOR (t:Tire) ON (t.vehicle_type)",
    "CREATE INDEX tire_nhom_lop            IF NOT EXISTS FOR (t:Tire) ON (t.nhom_lop)",
    "CREATE INDEX tire_co_sam              IF NOT EXISTS FOR (t:Tire) ON (t.co_sam)",
    "CREATE INDEX tire_gia_ban             IF NOT EXISTS FOR (t:Tire) ON (t.gia_ban_co_vat)",
    "CREATE INDEX tire_tai_trong           IF NOT EXISTS FOR (t:Tire) ON (t.tai_trong_lon_nhat)",
    "CREATE INDEX tire_dong_series         IF NOT EXISTS FOR (t:Tire) ON (t.dong_series)",
]


def ensure_schema(db: Neo4jClient):
    for stmt in _SCHEMA_STATEMENTS:
        db.run(stmt)
    print("  ✓ Schema constraints & indexes sẵn sàng")


# ══════════════════════════════════════════════════════════════════════════════
#  LOADER CLASS
# ══════════════════════════════════════════════════════════════════════════════

class TireKnowledgeGraphLoader:
    """
    Nạp toàn bộ dữ liệu từ file Excel vào Neo4j KG.

    Thứ tự quan trọng:
      1. Lốp (Tire nodes) phải được tạo trước
      2. Săm (Tube nodes) sau — cần match Tire
      3. tire_variant / quality_standard sau cùng — cần Tire + TirePattern
    """

    def __init__(self, excel_path: str = EXCEL_FILE):
        self.xl = pd.ExcelFile(excel_path)
        self.db = Neo4jClient()

    # ── private ───────────────────────────────────────────────────────────────

    def _read(self, sheet: str) -> pd.DataFrame:
        df = pd.read_excel(self.xl, sheet_name=sheet)
        print(f"    Đọc [{sheet}]: {len(df)} dòng × {len(df.columns)} cột")
        return df

    # ─────────────────────────────────────────────────────────────────────────
    #  1. LOP_XM_DPLUS
    # ─────────────────────────────────────────────────────────────────────────
    # 53 dòng, 23 cột.
    # Key notes:
    #   - Nhóm lốp: 'Motorcycle' | 'Scooter'
    #   - Cấu trúc lốp: 'Normal' | 'Millimetric'
    #   - Dòng series: NaN | 70.0 | 80.0 | 90.0  (lưu dưới dạng int: 70/80/90)
    #   - Kiểu hoa: hỗn hợp str ('D354','D355'…) và int (118,119,121,367…)
    #     → chuẩn hoá hết thành str
    #   - Chỉ số tải & tốc độ: tên cột có dấu & (không phải "tốc")
    #   - Giá: 52/53 dòng có NaN giá bán → lưu None
    # ─────────────────────────────────────────────────────────────────────────

    _CYPHER_LOP_XM = """
    UNWIND $rows AS row

    MERGE (t:Tire {size: row.size, brand: row.brand})
    SET
        t.vehicle_type          = row.vehicle_type,
        t.nhom_lop              = row.nhom_lop,
        t.cau_truc_lop          = row.cau_truc_lop,
        t.dong_series           = row.dong_series,
        t.kieu_quy_cach         = row.kieu_quy_cach,
        t.kieu_hoa              = row.kieu_hoa,
        t.co_sam                = row.co_sam,
        t.duong_kinh_vanh       = row.duong_kinh_vanh,
        t.rong_vanh_tieu_chuan  = row.rong_vanh_tieu_chuan,
        t.rong_vanh_thich_hop   = row.rong_vanh_thich_hop,
        t.duong_kinh_ngoai      = row.duong_kinh_ngoai,
        t.chieu_rong_toan_bo    = row.chieu_rong_toan_bo,
        t.chieu_sau_hoa         = row.chieu_sau_hoa,
        t.so_lop_bo             = row.so_lop_bo,
        t.phan_loai_tai         = row.phan_loai_tai,
        t.chi_so_tai_toc_do     = row.chi_so_tai_toc_do,
        t.tai_trong_lon_nhat    = row.tai_trong_lon_nhat,
        t.noi_ap_tieu_chuan     = row.noi_ap_tieu_chuan,
        t.toc_do_toi_da         = row.toc_do_toi_da,
        t.gia_nhap_chua_vat     = row.gia_nhap_chua_vat,
        t.gia_nhap_co_vat       = row.gia_nhap_co_vat,
        t.gia_ban_chua_vat      = row.gia_ban_chua_vat,
        t.gia_ban_co_vat        = row.gia_ban_co_vat

    // TirePattern node (chỉ tạo khi có kiểu hoa)
    WITH t, row WHERE row.kieu_hoa IS NOT NULL
    MERGE (p:TirePattern {pattern: row.kieu_hoa})

    // TireType node
    WITH t, p, row WHERE row.nhom_lop IS NOT NULL
    MERGE (tt:TireType {name: row.nhom_lop})

    MERGE (t)-[:CÓ_HOA]->(p)
    MERGE (t)-[:THUỘC_NHÓM]->(tt)
    """

    def _build_lop_xm_row(self, r, brand: str) -> dict:
        """Tạo dict row chuẩn cho lốp xe máy (dùng chung DPLUS & DRC)."""
        nhom = clean(r["Nhóm lốp"])
        # vehicle_type chi tiết hơn nhom_lop
        if nhom == "Scooter":
            vtype = "scooter"
        else:
            vtype = "motorcycle"

        # Dòng series: 70.0/80.0/90.0 → int 70/80/90, NaN → None
        series_raw = r.get("Dòng series")
        dong_series = int(clean_num(series_raw)) if not _is_nan(series_raw) else None

        return {
            "size":                 parse_size(r["Giá trị quy cách"]),
            "brand":                brand,
            "vehicle_type":         vtype,
            "nhom_lop":             nhom,
            "cau_truc_lop":         clean(r["Cấu trúc lốp"]),
            "dong_series":          dong_series,
            "kieu_quy_cach":        clean(r["Kiểu quy cách"]),
            # Kiểu hoa: int (119) hoặc str ('D354') → chuẩn hoá thành str
            "kieu_hoa":             clean_pattern(r["Kiểu hoa"]),
            "co_sam":               clean_bool(r["Có săm"]),
            "duong_kinh_vanh":      clean_num(r.get("Đường kính vành")),
            "rong_vanh_tieu_chuan": clean_num(r.get("Rộng vành tiêu chuẩn")),
            "rong_vanh_thich_hop":  clean(r.get("Rộng vành thích hợp")),
            "duong_kinh_ngoai":     clean_num(r.get("Đường kính ngoài")),
            "chieu_rong_toan_bo":   clean_num(r.get("Chiều rộng toàn bộ")),
            # Cột tên nhất quán sau khi cập nhật: đều là 'Chiều sâu hoa'
            "chieu_sau_hoa":        clean_num(r.get("Chiều sâu hoa")),
            "so_lop_bo":            clean(r.get("Số lớp bố")),
            "phan_loai_tai":        clean(r.get("Phân loại tải")),
            # Tên cột chính xác: 'Chỉ số tải & tốc độ' (dấu &)
            "chi_so_tai_toc_do":    clean(r.get("Chỉ số tải & tốc độ")),
            "tai_trong_lon_nhat":   clean_num(r.get("Tải trọng lớn nhất")),
            "noi_ap_tieu_chuan":    clean_num(r.get("Nội áp tiêu chuẩn")),
            "toc_do_toi_da":        clean_num(r.get("Tốc độ tối đa")),
            "gia_nhap_chua_vat":    clean_num(r.get("Giá nhập chưa VAT")),
            "gia_nhap_co_vat":      clean_num(r.get("Giá nhập có VAT")),
            "gia_ban_chua_vat":     clean_num(r.get("Giá bán chưa VAT")),
            "gia_ban_co_vat":       clean_num(r.get("Giá bán có VAT")),
        }

    def load_lop_xm_dplus(self):
        print("\n  [1/8] LOP_XM_DPLUS — Lốp xe máy DPLUS")
        df = self._read("LOP_XM_DPLUS")
        rows = [self._build_lop_xm_row(r, "DPLUS") for _, r in df.iterrows()]
        self.db.run(self._CYPHER_LOP_XM, {"rows": rows})
        print(f"    → Nạp {len(rows)} lốp DPLUS  "
              f"(Motorcycle: {sum(1 for r in rows if r['nhom_lop']=='Motorcycle')}, "
              f"Scooter: {sum(1 for r in rows if r['nhom_lop']=='Scooter')})")

    # ─────────────────────────────────────────────────────────────────────────
    #  2. LOP_XM_DRC
    # ─────────────────────────────────────────────────────────────────────────
    # 25 dòng, 23 cột. Tên cột ĐÃ ĐỒNG NHẤT với DPLUS sau khi cập nhật:
    #   - 'Chiều sâu hoa' (không còn '(mm)' nữa)
    #   - 'Chỉ số tải & tốc độ' giống DPLUS
    # Key notes:
    #   - Nhóm lốp: chỉ 'Motorcycle'
    #   - Cấu trúc lốp: 'Normal' | 'Millimetric ' (có dấu cách thừa → clean xử lý)
    #   - Kiểu hoa: toàn số nguyên (301,311,315,318,322,327,339…366,367)
    #   - Đường kính vành: lưu dưới dạng mm thực (431.8, 457.2, 482.6, 355.6)
    #     không phải inch → giữ nguyên float, không ép về int
    #   - Giá bán: TẤT CẢ 25 dòng đều NaN → lưu None
    # ─────────────────────────────────────────────────────────────────────────

    def load_lop_xm_drc(self):
        print("\n  [2/8] LOP_XM_DRC — Lốp xe máy DRC")
        df = self._read("LOP_XM_DRC")
        rows = [self._build_lop_xm_row(r, "DRC") for _, r in df.iterrows()]
        self.db.run(self._CYPHER_LOP_XM, {"rows": rows})
        print(f"    → Nạp {len(rows)} lốp DRC  "
              f"(co_sam=True: {sum(1 for r in rows if r['co_sam'] is True)}, "
              f"co_sam=False: {sum(1 for r in rows if r['co_sam'] is False)})")

    # ─────────────────────────────────────────────────────────────────────────
    #  3. LOP_XD_DRC
    # ─────────────────────────────────────────────────────────────────────────
    # 21 dòng, 15 cột.
    # Key notes:
    #   - Không có: co_sam, nhom_lop, so_lop_bo, toc_do_toi_da, phan_loai_tai
    #   - Có thêm: Loại xe đạp (Normal/Electric), Vành, Chiều rộng vành
    #   - Kiểu hoa: hỗn hợp int (117,205,216,217,219,228,230,517)
    #     và str ('D208','D210','D215') → chuẩn hoá thành str
    #   - TireType = Loại xe đạp (Normal / Electric)
    #   - vehicle_type = 'bicycle'
    # ─────────────────────────────────────────────────────────────────────────

    def load_lop_xd_drc(self):
        print("\n  [3/8] LOP_XD_DRC — Lốp xe đạp DRC")
        df = self._read("LOP_XD_DRC")

        cypher = """
        UNWIND $rows AS row

        MERGE (t:Tire {size: row.size, brand: 'DRC'})
        SET
            t.vehicle_type       = 'bicycle',
            t.nhom_lop           = 'bicycle',
            t.loai_xe_dap        = row.loai_xe_dap,
            t.vanh               = row.vanh,
            t.kieu_quy_cach      = row.kieu_quy_cach,
            t.kieu_hoa           = row.kieu_hoa,
            t.duong_kinh_ngoai   = row.duong_kinh_ngoai,
            t.chieu_rong_toan_bo = row.chieu_rong_toan_bo,
            t.duong_kinh_vanh    = row.duong_kinh_vanh,
            t.chieu_rong_vanh    = row.chieu_rong_vanh,
            t.noi_ap_tieu_chuan  = row.noi_ap_tieu_chuan,
            t.tai_trong_lon_nhat = row.tai_trong_lon_nhat,
            t.gia_nhap_chua_vat  = row.gia_nhap_chua_vat,
            t.gia_nhap_co_vat    = row.gia_nhap_co_vat,
            t.gia_ban_chua_vat   = row.gia_ban_chua_vat,
            t.gia_ban_co_vat     = row.gia_ban_co_vat

        WITH t, row WHERE row.kieu_hoa IS NOT NULL
        MERGE (p:TirePattern {pattern: row.kieu_hoa})

        WITH t, p, row WHERE row.loai_xe_dap IS NOT NULL
        MERGE (tt:TireType {name: row.loai_xe_dap})

        MERGE (t)-[:CÓ_HOA]->(p)
        MERGE (t)-[:THUỘC_NHÓM]->(tt)
        """

        rows = []
        for _, r in df.iterrows():
            rows.append({
                "size":               parse_size(r["Giá trị quy cách"]),
                "loai_xe_dap":        clean(r["Loại xe đạp"]),
                "vanh":               clean(r["Vành"]),
                "kieu_quy_cach":      clean(r["Kiểu quy cách"]),
                "kieu_hoa":           clean_pattern(r["Kiểu hoa"]),
                "duong_kinh_ngoai":   clean_num(r.get("Đường kính ngoài")),
                "chieu_rong_toan_bo": clean_num(r.get("Chiều rộng toàn bộ")),
                "duong_kinh_vanh":    clean_num(r.get("Đường kính vành")),
                "chieu_rong_vanh":    clean_num(r.get("Chiều rộng vành")),
                "noi_ap_tieu_chuan":  clean_num(r.get("Nội áp tiêu chuẩn")),
                "tai_trong_lon_nhat": clean_num(r.get("Tải trọng lớn nhất")),
                "gia_nhap_chua_vat":  clean_num(r.get("Giá nhập chưa VAT")),
                "gia_nhap_co_vat":    clean_num(r.get("Giá nhập có VAT")),
                "gia_ban_chua_vat":   clean_num(r.get("Giá bán chưa VAT")),
                "gia_ban_co_vat":     clean_num(r.get("Giá bán có VAT")),
            })

        self.db.run(cypher, {"rows": rows})
        print(f"    → Nạp {len(rows)} lốp xe đạp DRC  "
              f"(Normal: {sum(1 for r in rows if r['loai_xe_dap']=='Normal')}, "
              f"Electric: {sum(1 for r in rows if r['loai_xe_dap']=='Electric')})")

    # ─────────────────────────────────────────────────────────────────────────
    #  4. SAM_XM  (Săm xe máy)
    # ─────────────────────────────────────────────────────────────────────────

    def load_sam_xm(self):
        print("\n  [4/8] SAM_XM — Săm xe máy")
        df = self._read("SAM_XM")

        cypher = """
        UNWIND $rows AS row

        MERGE (tube:Tube {size: row.size, vehicle_type: 'motorcycle'})
        SET
            tube.kieu_quy_cach      = row.kieu_quy_cach,
            tube.chieu_rong_gap_doi = row.chieu_rong_gap_doi,
            tube.chieu_day_gap_doi  = row.chieu_day_gap_doi,
            tube.gia_nhap_chua_vat  = row.gia_nhap_chua_vat,
            tube.gia_nhap_co_vat    = row.gia_nhap_co_vat,
            tube.gia_ban_chua_vat   = row.gia_ban_chua_vat,
            tube.gia_ban_co_vat     = row.gia_ban_co_vat

        WITH tube, row
        MATCH (t:Tire)
        WHERE t.size = row.size
          AND t.co_sam = true
          AND (t.vehicle_type = 'motorcycle' OR t.vehicle_type = 'scooter')
        MERGE (tube)-[:DÙNG_CHO]->(t)
        """

        rows = []
        for _, r in df.iterrows():
            rows.append({
                "size":               parse_size(r["Giá trị quy cách"]),
                "kieu_quy_cach":      clean(r["Kiểu quy cách"]),
                "chieu_rong_gap_doi": clean_num(r.get("Chiều rộng gấp đôi")),
                "chieu_day_gap_doi":  clean_num(r.get("Chiều dày gấp đôi")),
                "gia_nhap_chua_vat":  clean_num(r.get("Giá nhập chưa VAT")),
                "gia_nhap_co_vat":    clean_num(r.get("Giá nhập có VAT")),
                "gia_ban_chua_vat":   clean_num(r.get("Giá bán chưa VAT")),
                "gia_ban_co_vat":     clean_num(r.get("Giá bán có VAT")),
            })

        self.db.run(cypher, {"rows": rows})
        print(f"    → Nạp {len(rows)} săm xe máy")

    # ─────────────────────────────────────────────────────────────────────────
    #  5. SAM_XD  (Săm xe đạp)
    # ─────────────────────────────────────────────────────────────────────────

    def load_sam_xd(self):
        print("\n  [5/8] SAM_XD — Săm xe đạp")
        df = self._read("SAM_XD")

        cypher = """
        UNWIND $rows AS row

        MERGE (tube:Tube {size: row.size, vehicle_type: 'bicycle'})
        SET
            tube.kieu_quy_cach      = row.kieu_quy_cach,
            tube.chieu_rong_gap_doi = row.chieu_rong_gap_doi,
            tube.chieu_day_gap_doi  = row.chieu_day_gap_doi,
            tube.gia_nhap_chua_vat  = row.gia_nhap_chua_vat,
            tube.gia_nhap_co_vat    = row.gia_nhap_co_vat,
            tube.gia_ban_chua_vat   = row.gia_ban_chua_vat,
            tube.gia_ban_co_vat     = row.gia_ban_co_vat

        WITH tube, row
        MATCH (t:Tire {vehicle_type: 'bicycle'})
        WHERE t.size = row.size
        MERGE (tube)-[:DÙNG_CHO]->(t)
        """

        rows = []
        for _, r in df.iterrows():
            rows.append({
                "size":               parse_size(r["Giá trị quy cách"]),
                "kieu_quy_cach":      clean(r["Kiểu quy cách"]),
                "chieu_rong_gap_doi": clean_num(r.get("Chiều rộng gấp đôi")),
                "chieu_day_gap_doi":  clean_num(r.get("Chiều dày gấp đôi")),
                "gia_nhap_chua_vat":  clean_num(r.get("Giá nhập chưa VAT")),
                "gia_nhap_co_vat":    clean_num(r.get("Giá nhập có VAT")),
                "gia_ban_chua_vat":   clean_num(r.get("Giá bán chưa VAT")),
                "gia_ban_co_vat":     clean_num(r.get("Giá bán có VAT")),
            })

        self.db.run(cypher, {"rows": rows})
        print(f"    → Nạp {len(rows)} săm xe đạp")

    # ─────────────────────────────────────────────────────────────────────────
    #  6. tire_variant
    # ─────────────────────────────────────────────────────────────────────────
    # 78 dòng, 3 cột: tire_size · pattern · brand
    # Key notes:
    #   - pattern: hỗn hợp int & str → clean_pattern
    #   - Một pattern có thể thuộc cả DRC lẫn DPLUS cùng lúc:
    #       ('2.25-17', 367) → DRC + DPLUS
    #       ('2.50-17', 367) → DRC + DPLUS
    #       ('2.75-17', 367) → DRC + DPLUS
    #   - Relationship mang thuộc tính brand để phân biệt
    # ─────────────────────────────────────────────────────────────────────────

    def load_tire_variant(self):
        print("\n  [6/8] tire_variant — Biến thể lốp × hoa × thương hiệu")
        df = self._read("tire_variant")

        cypher = """
        UNWIND $rows AS row

        // Chỉ xử lý khi Tire tồn tại
        MATCH (t:Tire {size: row.tire_size, brand: row.brand})

        // Đảm bảo TirePattern node tồn tại
        MERGE (p:TirePattern {pattern: row.pattern})

        // Relationship mang brand để phân biệt DRC/DPLUS dùng cùng pattern
        MERGE (t)-[r:CÓ_BIẾN_THỂ]->(p)
        SET r.brand = row.brand
        """

        rows = []
        skipped = 0
        for _, r in df.iterrows():
            p = clean_pattern(r["pattern"])
            s = parse_size(r["tire_size"])
            b = clean(r["brand"])
            if not p or not s or not b:
                skipped += 1
                continue
            rows.append({"tire_size": s, "pattern": p, "brand": b})

        self.db.run(cypher, {"rows": rows})
        print(f"    → Nạp {len(rows)} tire_variant relationships"
              + (f" ({skipped} bỏ qua do thiếu dữ liệu)" if skipped else ""))

    # ─────────────────────────────────────────────────────────────────────────
    #  7. variant_quality_standard
    # ─────────────────────────────────────────────────────────────────────────
    # 101 dòng, 3 cột: tire_size · pattern · standard
    # Key notes:
    #   - KHÔNG có cột brand → match Tire theo size + kieu_hoa
    #   - pattern: hỗn hợp int & str → clean_pattern
    #   - standard: 'JIS' (72 dòng) và 'QCVN36' (29 dòng)
    #   - Một Tire có thể đạt cả JIS lẫn QCVN36
    # ─────────────────────────────────────────────────────────────────────────

    def load_variant_quality_standard(self):
        print("\n  [7/8] variant_quality_standard — Tiêu chuẩn chất lượng")
        df = self._read("variant_quality_standard")

        cypher = """
        UNWIND $rows AS row

        // Upsert QualityStandard
        MERGE (qs:QualityStandard {name: row.standard})

        // Match Tire theo size + kieu_hoa (không cần brand vì sheet không có)
        WITH qs, row
        MATCH (t:Tire)
        WHERE t.size = row.tire_size AND t.kieu_hoa = row.pattern

        MERGE (t)-[:ĐẠT_CHUẨN]->(qs)
        """

        rows = []
        skipped = 0
        for _, r in df.iterrows():
            p = clean_pattern(r["pattern"])
            s = parse_size(r["tire_size"])
            std = clean(r["standard"])
            if not p or not s or not std:
                skipped += 1
                continue
            rows.append({"tire_size": s, "pattern": p, "standard": std})

        self.db.run(cypher, {"rows": rows})
        jis    = sum(1 for r in rows if r["standard"] == "JIS")
        qcvn   = sum(1 for r in rows if r["standard"] == "QCVN36")
        print(f"    → Nạp {len(rows)} quality relationships  "
              f"(JIS: {jis}, QCVN36: {qcvn})"
              + (f" ({skipped} bỏ qua)" if skipped else ""))

    # ─────────────────────────────────────────────────────────────────────────
    #  8. tube_brand + tube_van
    # ─────────────────────────────────────────────────────────────────────────

    def load_tube_accessories(self):
        print("\n  [8/8] tube_brand + tube_van — Thương hiệu & van săm")

        # tube_brand: (Brand)-[:SẢN_XUẤT_SĂM]->(Tube)
        tb = self._read("tube_brand")
        cypher_tb = """
        UNWIND $rows AS row
        MERGE (b:Brand {name: row.name_brand})
        WITH b, row
        MATCH (tube:Tube {size: row.tube_size})
        MERGE (b)-[:SẢN_XUẤT_SĂM]->(tube)
        """
        rows_tb = [
            {"tube_size": parse_size(r["tube_size"]), "name_brand": clean(r["name_brand"])}
            for _, r in tb.iterrows()
            if not _is_nan(r["tube_size"]) and not _is_nan(r["name_brand"])
        ]
        self.db.run(cypher_tb, {"rows": rows_tb})
        print(f"    → Nạp {len(rows_tb)} tube_brand relationships")

        # tube_van: (Tube)-[:DÙNG_VAN]->(Van)
        tv = self._read("tube_van")
        cypher_tv = """
        UNWIND $rows AS row
        MERGE (v:Van {name: row.name_van})
        WITH v, row
        MATCH (tube:Tube {size: row.tube_size})
        MERGE (tube)-[:DÙNG_VAN]->(v)
        """
        rows_tv = [
            {"tube_size": parse_size(r["tube_size"]), "name_van": clean(r["name_van"])}
            for _, r in tv.iterrows()
            if not _is_nan(r["tube_size"]) and not _is_nan(r["name_van"])
        ]
        self.db.run(cypher_tv, {"rows": rows_tv})
        print(f"    → Nạp {len(rows_tv)} tube_van relationships")

    # ─────────────────────────────────────────────────────────────────────────
    #  MASTER LOADER
    # ─────────────────────────────────────────────────────────────────────────

    def load_all(self):
        print("\n" + "═" * 62)
        print("  TIRE KNOWLEDGE GRAPH — BẮT ĐẦU NẠP DỮ LIỆU")
        print("═" * 62)

        # Lốp phải được tạo trước mọi thứ khác
        self.load_lop_xm_dplus()
        self.load_lop_xm_drc()
        self.load_lop_xd_drc()
        # Săm sau (cần Tire đã tồn tại)
        self.load_sam_xm()
        self.load_sam_xd()
        # Quan hệ sau cùng (cần Tire + TirePattern)
        self.load_tire_variant()
        self.load_variant_quality_standard()
        self.load_tube_accessories()

        print("\n" + "═" * 62)
        self._print_stats()
        print("\n  ✅  TẤT CẢ DỮ LIỆU ĐÃ NẠP THÀNH CÔNG!")
        print("═" * 62 + "\n")

    def _print_stats(self):
        checks = [
            # Node counts
            ("Node  Tire",             "MATCH (n:Tire) RETURN count(n) AS c"),
            ("Node  TirePattern",      "MATCH (n:TirePattern) RETURN count(n) AS c"),
            ("Node  TireType",         "MATCH (n:TireType) RETURN count(n) AS c"),
            ("Node  QualityStandard",  "MATCH (n:QualityStandard) RETURN count(n) AS c"),
            ("Node  Tube",             "MATCH (n:Tube) RETURN count(n) AS c"),
            ("Node  Brand",            "MATCH (n:Brand) RETURN count(n) AS c"),
            ("Node  Van",              "MATCH (n:Van) RETURN count(n) AS c"),
            # Rel counts
            ("Rel   CÓ_HOA",           "MATCH ()-[r:CÓ_HOA]->() RETURN count(r) AS c"),
            ("Rel   THUỘC_NHÓM",       "MATCH ()-[r:THUỘC_NHÓM]->() RETURN count(r) AS c"),
            ("Rel   CÓ_BIẾN_THỂ",      "MATCH ()-[r:CÓ_BIẾN_THỂ]->() RETURN count(r) AS c"),
            ("Rel   ĐẠT_CHUẨN",        "MATCH ()-[r:ĐẠT_CHUẨN]->() RETURN count(r) AS c"),
            ("Rel   DÙNG_CHO",         "MATCH ()-[r:DÙNG_CHO]->() RETURN count(r) AS c"),
            ("Rel   DÙNG_VAN",         "MATCH ()-[r:DÙNG_VAN]->() RETURN count(r) AS c"),
            ("Rel   SẢN_XUẤT_SĂM",     "MATCH ()-[r:SẢN_XUẤT_SĂM]->() RETURN count(r) AS c"),
            # Brand breakdown
            ("  Tire DPLUS",           "MATCH (t:Tire {brand:'DPLUS'}) RETURN count(t) AS c"),
            ("  Tire DRC",             "MATCH (t:Tire {brand:'DRC'}) RETURN count(t) AS c"),
            ("  Tire motorcycle",      "MATCH (t:Tire {vehicle_type:'motorcycle'}) RETURN count(t) AS c"),
            ("  Tire scooter",         "MATCH (t:Tire {vehicle_type:'scooter'}) RETURN count(t) AS c"),
            ("  Tire bicycle",         "MATCH (t:Tire {vehicle_type:'bicycle'}) RETURN count(t) AS c"),
        ]
        print("  📊 THỐNG KÊ KNOWLEDGE GRAPH:")
        for label, q in checks:
            result = self.db.run(q)
            count  = result[0]["c"] if result else 0
            print(f"    {label:<24} : {count:>4}")

    def close(self):
        self.db.close()


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    loader = TireKnowledgeGraphLoader(EXCEL_FILE)
    try:
        ensure_schema(loader.db)
        loader.load_all()
    finally:
        loader.close()