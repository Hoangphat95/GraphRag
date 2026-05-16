import re
from typing import Dict, Any, Optional, List

class TireQueryHandler:
    def __init__(self, conn):
        self.conn = conn
        self.query_map = {
            'size': """
            MATCH (t:Tire {size: $size})
            OPTIONAL MATCH (t)-[:CÓ_MÃ]->(p:TirePattern)
            RETURN t, p
            """,
            'brand_size': """
            MATCH (t:Tire {brand: $brand, size: $size})
            OPTIONAL MATCH (t)-[:CÓ_MÃ]->(p)
            RETURN t, p
            """,
            'all_brand': """
            MATCH (t:Tire {brand: $brand})-[:CÓ_MÃ]->(p)
            RETURN t, p
            ORDER BY t.size
            """,
            'vehicle_type': """
            MATCH (t:Tire {vehicle_type: $vehicle_type})
            OPTIONAL MATCH (t)-[:CÓ_MÃ]->(p:TirePattern)
            OPTIONAL MATCH (t)-[:THUỘC_LOẠI]->(tt:TireType)
            RETURN t, p, tt
            ORDER BY t.size
            """,
            'pattern': """
            MATCH (t:Tire)-[:CÓ_MÃ]->(p:TirePattern {pattern: $pattern})
            OPTIONAL MATCH (t)-[:THUỘC_LOẠI]->(tt:TireType)
            OPTIONAL MATCH (t)-[:ĐẠT_CHUẨN]->(qs:QualityStandard)
            RETURN t, p, tt, qs
            """,
            'quality_standard': """
            MATCH (t:Tire)-[:ĐẠT_CHUẨN]->(qs:QualityStandard {name: $standard})
            OPTIONAL MATCH (t)-[:CÓ_MÃ]->(p:TirePattern)
            OPTIONAL MATCH (t)-[:THUỘC_LOẠI]->(tt:TireType)
            RETURN t, p, tt, qs
            """,
            'price_range': """
            MATCH (t:Tire)
            WHERE t.gia_ban_co_vat >= $min_price AND t.gia_ban_co_vat <= $max_price
            OPTIONAL MATCH (t)-[:CÓ_MÃ]->(p:TirePattern)
            OPTIONAL MATCH (t)-[:THUỘC_LOẠI]->(tt:TireType)
            RETURN t, p, tt
            ORDER BY t.gia_ban_co_vat
            """,
            'load_capacity': """
            MATCH (t:Tire)
            WHERE t.tai_trong_lon_nhat >= $min_load
            OPTIONAL MATCH (t)-[:CÓ_MÃ]->(p:TirePattern)
            OPTIONAL MATCH (t)-[:THUỘC_LOẠI]->(tt:TireType)
            RETURN t, p, tt
            ORDER BY t.tai_trong_lon_nhat DESC
            """,
            'brand_patterns': """
            MATCH (t:Tire {brand: $brand})-[:CÓ_MÃ]->(p:TirePattern)
            RETURN DISTINCT p
            """,
            'alternative_tires': """
            MATCH (t:Tire {size: $size, brand: $current_brand})
            WITH t
            MATCH (other:Tire {size: $size})
            WHERE other.brand <> $current_brand
            OPTIONAL MATCH (other)-[:CÓ_MÃ]->(p:TirePattern)
            OPTIONAL MATCH (other)-[:THUỘC_LOẠI]->(tt:TireType)
            RETURN other, p, tt
            """,
            'bicycle_rim': """
            MATCH (t:Tire {vehicle_type: 'bicycle', vanh: $rim_type})
            OPTIONAL MATCH (t)-[:CÓ_MÃ]->(p:TirePattern)
            OPTIONAL MATCH (t)-[:THUỘC_LOẠI]->(tt:TireType)
            RETURN t, p, tt
            ORDER BY t.size
            """,
            'max_speed': """
            MATCH (t:Tire)
            WHERE toInteger(t.toc_do_toi_da) >= $min_speed
            AND ($brand IS NULL OR t.brand = $brand)
            OPTIONAL MATCH (t)-[:CÓ_MÃ]->(p:TirePattern)
            OPTIONAL MATCH (t)-[:THUỘC_LOẠI]->(tt:TireType)
            RETURN t, p, tt
            ORDER BY toInteger(t.toc_do_toi_da) DESC
            """,
            'pressure_range': """
            MATCH (t:Tire)
            WHERE t.noi_ap_tieu_chuan >= $min_pressure AND t.noi_ap_tieu_chuan <= $max_pressure
            OPTIONAL MATCH (t)-[:CÓ_MÃ]->(p:TirePattern)
            OPTIONAL MATCH (t)-[:THUỘC_LOẠI]->(tt:TireType)
            RETURN t, p, tt
            ORDER BY t.noi_ap_tieu_chuan
            """,
            'price_comparison': """
            MATCH (t:Tire {size: $size})
            OPTIONAL MATCH (t)-[:CÓ_MÃ]->(p:TirePattern)
            RETURN t, p
            ORDER BY t.gia_ban_co_vat
            """,
            'tire_group': """
            MATCH (t:Tire {nhom_lop: $nhom_lop})
            OPTIONAL MATCH (t)-[:CÓ_MÃ]->(p:TirePattern)
            OPTIONAL MATCH (t)-[:THUỘC_LOẠI]->(tt:TireType)
            RETURN t, p, tt
            ORDER BY t.size
            """,
            'with_tube': """
            MATCH (t:Tire {co_sam: true})
            OPTIONAL MATCH (t)-[:CÓ_MÃ]->(p:TirePattern)
            OPTIONAL MATCH (t)-[:THUỘC_LOẠI]->(tt:TireType)
            RETURN t, p, tt
            ORDER BY t.size
            """,
            'stats_by_brand': """
            MATCH (t:Tire)
            RETURN t.brand as brand, count(t) as total_tires
            ORDER BY total_tires DESC
            """,
            'stats_by_vehicle': """
            MATCH (t:Tire)
            RETURN t.vehicle_type as vehicle_type, count(t) as total_tires
            ORDER BY total_tires DESC
            """,
            'rim_diameter': """
            MATCH (t:Tire)
            WHERE t.duong_kinh_vanh = $rim_diameter
            OPTIONAL MATCH (t)-[:CÓ_MÃ]->(p:TirePattern)
            OPTIONAL MATCH (t)-[:THUỘC_LOẠI]->(tt:TireType)
            RETURN t, p, tt
            ORDER BY t.size
            """
        }
    
    def _extract_size(self, text: str) -> Optional[str]:
        """Extract tire size from text"""
        size_pattern = r'(\d+\.?\d*/?\d+-\d+|\d+\.?\d+-\d+)'
        match = re.search(size_pattern, text)
        return match.group(1) if match else None
    
    def _extract_brand(self, text: str) -> Optional[str]:
        """Extract brand from text"""
        brand_pattern = r'\b(dplus|drc)\b'
        match = re.search(brand_pattern, text, re.IGNORECASE)
        return match.group(1).upper() if match else None
    
    def _extract_numbers(self, text: str) -> List[int]:
        """Extract all numbers from text"""
        return [int(num) for num in re.findall(r'\d+', text)]
    
    def _detect_query_type(self, text: str) -> str:
        """Detect query type based on keywords"""
        text_lower = text.lower()
        
        # Priority order for detection
        if any(word in text_lower for word in ['xe đạp', 'bicycle', 'đạp']):
            return 'vehicle_type'
        elif 'pattern' in text_lower or 'mã' in text_lower:
            return 'pattern'
        elif any(word in text_lower for word in ['chất lượng', 'tiêu chuẩn', 'jis']):
            return 'quality_standard'
        elif any(word in text_lower for word in ['giá', 'price', 'k', 'đồng']):
            return 'price_range'
        elif any(word in text_lower for word in ['tải trọng', 'load', 'trọng']):
            return 'load_capacity'
        elif any(word in text_lower for word in ['thay thế', 'thay', 'alternative']):
            return 'alternative_tires'
        elif any(word in text_lower for word in ['vành', 'rim']):
            return 'bicycle_rim'
        elif any(word in text_lower for word in ['tốc độ', 'speed']):
            return 'max_speed'
        elif any(word in text_lower for word in ['áp suất', 'pressure']):
            return 'pressure_range'
        elif any(word in text_lower for word in ['so sánh', 'compare']):
            return 'price_comparison'
        elif any(word in text_lower for word in ['nhóm', 'group']):
            return 'tire_group'
        elif any(word in text_lower for word in ['săm', 'tube']):
            return 'with_tube'
        elif any(word in text_lower for word in ['thống kê', 'stats', 'count']):
            if 'brand' in text_lower:
                return 'stats_by_brand'
            else:
                return 'stats_by_vehicle'
        elif 'inch' in text_lower and self._extract_numbers(text):
            return 'rim_diameter'
        elif 'đường kính' in text_lower or 'diameter' in text_lower:
            return 'rim_diameter'
        elif self._extract_brand(text) and self._extract_size(text):
            return 'brand_size'
        elif self._extract_brand(text):
            return 'all_brand'
        elif self._extract_size(text):
            return 'size'
        
        return 'size'  # default
    
    def _build_params(self, query_type: str, text: str) -> Dict[str, Any]:
        """Build parameters for the query"""
        params = {}
        text_lower = text.lower()
        
        if query_type == 'vehicle_type':
            if 'xe đạp' in text_lower or 'bicycle' in text_lower:
                params['vehicle_type'] = 'bicycle'
            else:
                params['vehicle_type'] = 'motorcycle'
        
        elif query_type == 'pattern':
            # Extract pattern (could be number or string)
            pattern_match = re.search(r'pattern\s+(\w+)', text_lower)
            if pattern_match:
                params['pattern'] = pattern_match.group(1).upper()
        
        elif query_type == 'quality_standard':
            if 'jis' in text_lower:
                params['standard'] = 'JIS'
            # Add more standards as needed
        
        elif query_type == 'price_range':
            numbers = self._extract_numbers(text)
            if len(numbers) >= 2:
                params['min_price'] = min(numbers)
                params['max_price'] = max(numbers)
            elif len(numbers) == 1:
                params['min_price'] = 0
                params['max_price'] = numbers[0]
        
        elif query_type == 'load_capacity':
            numbers = self._extract_numbers(text)
            if numbers:
                params['min_load'] = min(numbers)
        
        elif query_type == 'alternative_tires':
            size = self._extract_size(text)
            brand = self._extract_brand(text)
            if size and brand:
                params['size'] = size
                params['current_brand'] = brand
        
        elif query_type == 'bicycle_rim':
            if 'thẳng' in text_lower or 'ss' in text_lower:
                params['rim_type'] = 'SS&CT (Thẳng và U)'
        
        elif query_type == 'max_speed':
            numbers = self._extract_numbers(text)
            if numbers:
                params['min_speed'] = min(numbers)
            params['brand'] = self._extract_brand(text)
        
        elif query_type == 'pressure_range':
            numbers = self._extract_numbers(text)
            if len(numbers) >= 2:
                params['min_pressure'] = min(numbers)
                params['max_pressure'] = max(numbers)
        
        elif query_type == 'price_comparison':
            size = self._extract_size(text)
            if size:
                params['size'] = size
        
        elif query_type == 'tire_group':
            if 'motorcycle' in text_lower or 'xe máy' in text_lower:
                params['nhom_lop'] = 'Motorcycle'
        
        elif query_type == 'rim_diameter':
            numbers = self._extract_numbers(text)
            if numbers:
                params['rim_diameter'] = numbers[0]
        
        elif query_type in ['brand_size', 'all_brand']:
            brand = self._extract_brand(text)
            if brand:
                params['brand'] = brand
            if query_type == 'brand_size':
                size = self._extract_size(text)
                if size:
                    params['size'] = size
        
        elif query_type == 'size':
            size = self._extract_size(text)
            if size:
                params['size'] = size
        
        return params
    
    def search_tire(self, query_text: str) -> Optional[tuple]:
        """Parse query và trả về (query_type, data)"""
        if not query_text or not query_text.strip():
            return None
        
        query_type = self._detect_query_type(query_text)
        params = self._build_params(query_type, query_text)
        
        if not params:
            return None
        
        query = self.query_map[query_type]
        if query_type == 'max_speed' and params.get('brand') is None:
            query = query.replace('AND ($brand IS NULL OR t.brand = $brand)', '')
            params.pop('brand', None)
        
        try:
            result = self.conn.run_query(query, params)
            return (query_type, result)
        except Exception as e:
            print(f"Query error: {e}")
            return None
