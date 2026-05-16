// Tạo các Node Labels và Relationships cho Knowledge Graph Lốp Xe

// Constraints cho uniqueness
CREATE CONSTRAINT tire_unique IF NOT EXISTS FOR (t:Tire) REQUIRE (t.size, t.brand) IS UNIQUE;
CREATE CONSTRAINT tire_pattern_unique IF NOT EXISTS FOR (p:TirePattern) REQUIRE p.pattern IS UNIQUE;
CREATE CONSTRAINT quality_standard_unique IF NOT EXISTS FOR (q:QualityStandard) REQUIRE q.name IS UNIQUE;
CREATE CONSTRAINT tire_type_unique IF NOT EXISTS FOR (tt:TireType) REQUIRE tt.name IS UNIQUE;

// Indexes cho query nhanh trên Tire nodes
CREATE INDEX tire_size IF NOT EXISTS FOR (t:Tire) ON (t.size);
CREATE INDEX tire_brand IF NOT EXISTS FOR (t:Tire) ON (t.brand);
CREATE INDEX tire_vehicle_type IF NOT EXISTS FOR (t:Tire) ON (t.vehicle_type);
CREATE INDEX tire_nhom_lop IF NOT EXISTS FOR (t:Tire) ON (t.nhom_lop);
CREATE INDEX tire_gia_ban IF NOT EXISTS FOR (t:Tire) ON (t.gia_ban_co_vat);
CREATE INDEX tire_tai_trong IF NOT EXISTS FOR (t:Tire) ON (t.tai_trong_lon_nhat);
CREATE INDEX tire_toc_do IF NOT EXISTS FOR (t:Tire) ON (t.toc_do_toi_da);
CREATE INDEX tire_ap_suat IF NOT EXISTS FOR (t:Tire) ON (t.noi_ap_tieu_chuan);
CREATE INDEX tire_duong_kinh_vanh IF NOT EXISTS FOR (t:Tire) ON (t.duong_kinh_vanh);
CREATE INDEX tire_co_sam IF NOT EXISTS FOR (t:Tire) ON (t.co_sam);

// Composite indexes cho queries phức tạp
CREATE INDEX tire_brand_size IF NOT EXISTS FOR (t:Tire) ON (t.brand, t.size);
CREATE INDEX tire_vehicle_size IF NOT EXISTS FOR (t:Tire) ON (t.vehicle_type, t.size);
CREATE INDEX tire_price_range IF NOT EXISTS FOR (t:Tire) ON (t.gia_ban_co_vat, t.brand);

// Indexes cho TirePattern
CREATE INDEX tire_pattern_name IF NOT EXISTS FOR (p:TirePattern) ON (p.pattern);

// Indexes cho QualityStandard
CREATE INDEX quality_standard_name IF NOT EXISTS FOR (q:QualityStandard) ON (q.name);

// Indexes cho TireType
CREATE INDEX tire_type_name IF NOT EXISTS FOR (tt:TireType) ON (tt.name);
