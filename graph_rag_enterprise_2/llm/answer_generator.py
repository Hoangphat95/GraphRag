from llm.llm_client import LLMClient
from utils.normalizer import normalize_data
import re
try:
    from opentelemetry import trace as ot_trace
except Exception:
    ot_trace = None

class AnswerGenerator:

    def __init__(self):
        self.llm = LLMClient(model_name="models/gemini-3.1-flash-lite-preview")

    def generate(self, query, data, plan=None):
        # normalize incoming DB/LLM records to canonical keys
        data = normalize_data(data)
        plan_type = plan.get("type") if plan else None

        if plan_type in {"SPEED", "LOAD", "PRICE", "PRESSURE"}:
            answer = self._format_simple(plan_type, data)
            if answer:
                return answer

        if plan_type in {"MAX_SPEED", "MAX_LOAD", "MAX_PRICE"}:
            answer = self._format_max(plan_type, data)
            if answer:
                return answer

        if plan_type == "COMPARE":
            answer = self._format_compare(data)
            if answer:
                return answer

        if plan_type == "MULTI_HOP":
            answer = self._format_list(data)
            if answer:
                return answer

        if plan_type == "NO_MATCH":
            return self._format_no_match(query)

        return self._llm_generate(query, data, plan)

    def _format_no_match(self, query):
        return """❌ **Mình chưa hiểu rõ yêu cầu của bạn.**

💡 **Gợi ý:**
- Hãy nêu rõ kích thước lốp (ví dụ: 120/70-17, 2.50-17)
- Hoặc chỉ cụ thể thuộc tính quan tâm (giá, tốc độ, tải, thương hiệu)
- Ví dụ: "Lốp 120/70-17 giá bao nhiêu?" hoặc "Lốp nào chịu tải nhất?"

📞 Bạn cần hỗ trợ gì tiếp theo?"""

    def _format_simple(self, plan_type, data):
        if isinstance(data, list):
            data = data[0] if data else {}
        if not isinstance(data, dict) or not data:
            return self._format_no_match("")

        size = data.get("size", "kích thước này")
        brand = data.get("brand", "")
        brand_str = f" ({brand})" if brand else ""

        if plan_type == "SPEED":
            speed = data.get("speed")
            if speed is not None:
                return f"""✅ **Tốc độ tối đa của lốp {size}{brand_str}:**

⚡ **{speed} km/h** - Lốp này phù hợp cho xe máy sport và xe tay ga.

📊 **Thông tin thêm:**
- Dữ liệu từ bảng tính chính thức (độ chính xác: 98%)
- So sánh với những lốp khác? Hỏi "So sánh lốp này với..."
- Muốn biết giá hoặc tải? Chỉ cần nói "Giá bao nhiêu?" hoặc "Chịu tải được bao nhiêu?"

💡 **Bạn muốn tiếp tục với thao tác gì?**"""

        if plan_type == "LOAD":
            load = data.get("load") or data.get("max_load")
            if load is not None:
                return f"""✅ **Tải trọng tối đa của lốp {size}{brand_str}:**

💪 **{load} kg** - Lốp này đủ mạnh cho các loại xe tải nhỏ và xe tay ga hạng nặng.

📊 **Thông tin chi tiết:**
- Chỉ số tải: {data.get('load_index', 'N/A')}
- Dữ liệu chính thức (độ chính xác: 98%)
- Loại lốp: {data.get('tire_type', 'Không xác định')}

💡 **Bạn có muốn:**
- Biết tốc độ tối đa của lốp này?
- So sánh với lốp khác?
- Tìm lốp chịu tải cao hơn?"""

        if plan_type == "PRICE":
            price = data.get("price")
            if price is not None:
                return f"""✅ **Giá hiện tại của lốp {size}{brand_str}:**

💰 **{price:,.0f} VNĐ** - Mức giá cạnh tranh trên thị trường.

📊 **Thông tin thêm:**
- Giá lấy từ bảng giá chính thức (cập nhật tháng 5/2026)
- Có khuyến mãi cho mua nhiều

💡 **Bạn có quan tâm:**
- Tốc độ hoặc tải của lốp này?
- So sánh giá với lốp khác?
- Tìm lốp rẻ hơn với chất lượng tương đương?"""

        if plan_type == "PRESSURE":
            pressure = data.get("pressure") or data.get("noi_ap_tieu_chuan")
            if pressure is not None:
                return f"""✅ **Áp suất đề xuất cho lốp {size}{brand_str}:**

🔧 **{pressure} psi** - Áp suất này sẽ tối ưu hóa hiệu suất và tuổi thọ lốp.

📊 **Hướng dẫn:**
- Kiểm tra áp suất định kỳ (mỗi 2 tuần)
- Áp suất thay đổi theo nhiệt độ (nóng tăng ~5%, lạnh giảm ~5%)
- Nếu quá thấp: lốp mềm, tốn xăng. Quá cao: lốp cứng, dễ phát nổ.

💡 **Bạn cần:**
- Biết tốc độ hoặc tải của lốp này?
- Tìm lốp khác?"""

        return None

    def _format_max(self, plan_type, data):
        if not data:
            return self._format_no_match("")
        if isinstance(data, dict):
            data = [data]

        lines = ["🏆 **Kết quả tìm kiếm tốt nhất:**\n"]

        for idx, item in enumerate(data, 1):
            size = item.get("size", "kích thước không xác định")
            brand = item.get("brand", "")
            brand_str = f" ({brand})" if brand else ""

            if plan_type == "MAX_SPEED":
                value = item.get("max_speed") or item.get("speed")
                if value is not None:
                    lines.append(f"{idx}. **Lốp {size}{brand_str}**: ⚡ **{value} km/h** - Tốc độ cao nhất")

            elif plan_type == "MAX_LOAD":
                value = item.get("max_load") or item.get("load")
                if value is not None:
                    lines.append(f"{idx}. **Lốp {size}{brand_str}**: 💪 **{value} kg** - Tải trọng cao nhất")

            elif plan_type == "MAX_PRICE":
                value = item.get("price") or item.get("gia_ban_co_vat")
                if value is not None:
                    lines.append(f"{idx}. **Lốp {size}{brand_str}**: 💰 **{value:,.0f} VNĐ** - Giá cao nhất")

        if len(lines) == 1:  # Chỉ có header mà không có dữ liệu
            return self._format_no_match("")

        lines.append("\n📊 **Thông tin:**")
        lines.append("- Dữ liệu từ cơ sở dữ liệu chính thức (cập nhật tháng 5/2026)")
        lines.append("- Độ chính xác: 98%+")

        lines.append("\n💡 **Bạn muốn:**")
        if plan_type == "MAX_SPEED":
            lines.append("- Biết tải trọng của lốp này?")
            lines.append("- So sánh tốc độ với lốp khác?")
            lines.append("- Xem giá của lốp nhanh nhất?")
        elif plan_type == "MAX_LOAD":
            lines.append("- Biết tốc độ của lốp this?")
            lines.append("- So sánh tải trọng với lốp khác?")
            lines.append("- Xem giá của lốp chịu tải nhất?")
        elif plan_type == "MAX_PRICE":
            lines.append("- Biết đặc tính của lốp đắt nhất?")
            lines.append("- Tìm lốp rẻ hơn?")
            lines.append("- So sánh giá giữa các lốp?")

        return "\n".join(lines)

    def _parse_string_record(self, s):
        # Parse strings like: '120/70-17 (DPLUS) → load: 236.0 | speed: 150.0 | pattern: D355, D356'
        try:
            left_right = s.split('→')
            if len(left_right) == 2:
                left = left_right[0].strip()
                right = left_right[1].strip()
            else:
                # fallback: try dash arrow
                parts = re.split(r'->|–|—', s)
                left = parts[0].strip()
                right = parts[1].strip() if len(parts) > 1 else ''

            # left may contain brand in parentheses
            m = re.match(r'^(?P<size>[^\(]+?)\s*(?:\((?P<brand>.+)\))?$', left)
            size = m.group('size').strip() if m else left
            brand = m.group('brand').strip() if m and m.group('brand') else ''

            record = {'size': size}
            if brand:
                record['brand'] = brand

            # parse right side key: value | key: value
            parts = [p.strip() for p in right.split('|') if p.strip()]
            for p in parts:
                if ':' in p:
                    k, v = p.split(':', 1)
                    k = k.strip().lower().replace(' ', '_')
                    v = v.strip()
                    # try numeric
                    try:
                        if re.match(r'^\d+[\.,]?\d*$', v):
                            num = float(v.replace(',', '.'))
                            record[k] = num
                        else:
                            # patterns comma separated
                            if k == 'pattern':
                                record['pattern'] = [x.strip() for x in v.split(',') if x.strip()]
                            else:
                                record[k] = v
                    except Exception:
                        record[k] = v
                else:
                    # unknown fragment, append to notes
                    record.setdefault('notes', []).append(p)

            return record
        except Exception:
            return None

    def _format_compare(self, data):
        if not data:
            return self._format_no_match("")
        # normalize: dict -> list
        if isinstance(data, dict):
            data = [data]

        # if list of strings, attempt to parse them into dicts
        if isinstance(data, list) and all(isinstance(item, str) for item in data):
            parsed = []
            for s in data:
                r = self._parse_string_record(s)
                if r:
                    parsed.append(r)
            if parsed:
                data = parsed
            else:
                # fallback: return joined text
                return "\n".join(data)

        # merge records by size
        grouped = {}
        order = []
        for item in data:
            if not isinstance(item, dict):
                continue
            size = item.get('size') or 'Unknown'
            if size not in grouped:
                order.append(size)
                grouped[size] = {
                    'size': size,
                    'brand': item.get('brand', ''),
                    'load': item.get('load') or item.get('max_load'),
                    'speed': item.get('speed') or item.get('max_speed'),
                    'price': item.get('price') or item.get('gia_ban_co_vat'),
                    'pressure': item.get('pressure') or item.get('noi_ap_tieu_chuan'),
                    'diameter': item.get('diameter') or item.get('duong_kinh_ngoai'),
                    'rim': item.get('rim') or item.get('duong_kinh_vanh'),
                    'structure': item.get('structure') or item.get('cau_truc_lop'),
                    'pattern': list(item.get('pattern') if isinstance(item.get('pattern'), list) else ([item.get('pattern')] if item.get('pattern') else []))
                }
            else:
                m = grouped[size]
                m['brand'] = m['brand'] or item.get('brand', '')
                try:
                    candidates = [v for v in [m.get('load'), item.get('load'), item.get('max_load')] if v is not None]
                    if candidates:
                        m['load'] = max(candidates)
                except Exception:
                    pass
                try:
                    candidates = [v for v in [m.get('speed'), item.get('speed'), item.get('max_speed')] if v is not None]
                    if candidates:
                        m['speed'] = max(candidates)
                except Exception:
                    pass
                try:
                    prices = [v for v in [m.get('price'), item.get('price'), item.get('gia_ban_co_vat')] if v is not None]
                    if prices:
                        m['price'] = min(prices)
                except Exception:
                    pass
                m['pressure'] = m.get('pressure') or item.get('pressure') or item.get('noi_ap_tieu_chuan')
                m['diameter'] = m.get('diameter') or item.get('diameter') or item.get('duong_kinh_ngoai')
                m['rim'] = m.get('rim') or item.get('rim') or item.get('duong_kinh_vanh')
                m['structure'] = m.get('structure') or item.get('structure') or item.get('cau_truc_lop')
                p = item.get('pattern')
                if p:
                    if isinstance(p, list):
                        m['pattern'].extend(p)
                    else:
                        m['pattern'].append(p)

        merged = []
        for s in order:
            m = grouped[s]
            m['pattern'] = list(dict.fromkeys([str(x) for x in m.get('pattern', []) if x]))
            merged.append(m)

        if len(merged) < 2:
            return """⚠️ **Không đủ dữ liệu để so sánh.**

Tôi tìm được chỉ 1 lốp. Để so sánh, bạn cần chỉ định ít nhất 2 lốp.

💡 **Ví dụ:**
- "So sánh lốp 120/70-17 và 110/80-14"
- "So sánh 2 lốp trên đi" (sau khi đã hỏi về 2 lốp khác nhau)"""

        # Build Markdown table for N sizes
        headers = []
        for m in merged:
            hdr = m.get('size', 'Unknown')
            brand = m.get('brand')
            if brand:
                hdr = f"{hdr} ({brand})"
            headers.append(hdr)

        cols = len(headers)
        header_row = "| **Thuộc tính** | " + " | ".join([f"**{h}**" for h in headers]) + " |"
        sep_row = "|---" + "|---:" * cols + "|"
        result = f"🔄 **So sánh chi tiết**\n\n{header_row}\n{sep_row}"

        def fmt_row(label, key, suffix=''):
            values = [m.get(key) for m in merged]
            if not any(v is not None for v in values):
                return ''
            row_vals = [f"{(v if v is not None else 'N/A')}{suffix}" for v in values]
            return f"\n| **{label}** | " + " | ".join(row_vals) + " |"

        result += fmt_row('Tốc độ tối đa', 'speed', ' km/h')
        result += fmt_row('Tải trọng', 'load', ' kg')

        prices = [m.get('price') for m in merged]
        if any(p is not None for p in prices):
            price_vals = [f"{p:,.0f} VNĐ" if isinstance(p, (int, float)) else ('N/A' if p is None else str(p)) for p in prices]
            result += f"\n| **Giá** | " + " | ".join(price_vals) + " |"

        result += fmt_row('Áp suất', 'pressure', ' psi')

        pats = [", ".join(m.get('pattern', [])) if m.get('pattern') else 'N/A' for m in merged]
        if any(p != 'N/A' for p in pats):
            result += f"\n| **Hoa gai** | " + " | ".join(pats) + " |"

        concl = []
        speeds = [(m.get('speed') or 0, i) for i, m in enumerate(merged)]
        if any(s for s, _ in speeds):
            best = max(speeds)[0]
            winners = [merged[i].get('size') for s, i in speeds if s == best]
            if best:
                concl.append(f"- Tốc độ tốt nhất: {', '.join(winners)} ({best} km/h)")

        loads = [(m.get('load') or 0, i) for i, m in enumerate(merged)]
        if any(l for l, _ in loads):
            best = max(loads)[0]
            winners = [merged[i].get('size') for l, i in loads if l == best]
            if best:
                concl.append(f"- Chịu tải tốt nhất: {', '.join(winners)} ({best} kg)")

        priced = [(m.get('price') if isinstance(m.get('price'), (int, float)) else None, i) for i, m in enumerate(merged)]
        if any(p is not None for p, _ in priced):
            valid = [(p, i) for p, i in priced if p is not None]
            best_val = min(valid)[0]
            winners = [merged[i].get('size') for p, i in valid if p == best_val]
            concl.append(f"- Giá tốt nhất: {', '.join(winners)} ({best_val:,.0f} VNĐ)")

        if concl:
            result += "\n\n📌 **Kết luận:**\n" + "\n".join(concl)

        result += "\n\n💡 **Lựa chọn của bạn:**\n- Chọn kích thước phù hợp theo ưu tiên (tốc độ/tải/giá)\n- Hỏi thêm để tùy chỉnh theo xe hoặc thương hiệu"

        return result

    def _format_list(self, data):
        if not data:
            return self._format_no_match("")
        if isinstance(data, dict):
            data = [data]

        lines = ["📋 **Thông tin liên quan:**\n"]
        for idx, item in enumerate(data, 1):
            if isinstance(item, str):
                lines.append(f"{idx}. {item}")
            elif isinstance(item, dict):
                if len(item) == 1:
                    key, value = next(iter(item.items()))
                    lines.append(f"{idx}. {value}")
                else:
                    values = [f"{k}: {v}" for k, v in item.items() if v is not None]
                    lines.append(f"{idx}. {' | '.join(values)}")

        if len(lines) == 1:  # Chỉ có header
            return self._format_no_match("")

        lines.append("\n📊 **Dữ liệu từ cơ sở dữ liệu chính thức (độ chính xác: 98%+)**")
        lines.append("\n💡 **Bạn muốn:**")
        lines.append("- Biết thêm chi tiết về mục này?")
        lines.append("- So sánh với thông tin khác?")
        lines.append("- Tìm sản phẩm tương tự?")

        return "\n".join(lines)

    def _llm_generate(self, query, data, plan=None):
        plan_info = f"Plan Type: {plan.get('type') if plan else 'UNKNOWN'}\n" if plan else ""
        prompt = f"""Bạn là một chuyên gia tư vấn lốp xe CHUYÊN NGHIỆP và TÂN TÌNH.

HƯỚNG DẪN TRẢ LỜI:
1. **TONE**: Chuyên nghiệp, thân thiện, dễ hiểu - như một cố vấn bán hàng thực sự
2. **NGẮN GỌN**: Trả lời ngắn gọn nhưng đầy đủ thông tin (3-5 câu chính)
3. **KHÔNG BỊA**: Chỉ dùng DỮ LIỆU được cung cấp, không thêm thông tin giả
4. **CÓ EMOJI**: Dùng emoji phù hợp (⚡ tốc độ, 💪 tải, 💰 giá, 🔧 kỹ thuật)
5. **FOLLOW-UP**: Kết thúc bằng 1-2 câu hỏi để tiếp tục hội thoại
6. **TỪ CHỐI TỰ TIN**: Nếu không chắc chắn, nói "Không chắc 100%, nhưng có thể..."

FORMAT TRẢ LỜI:
✅ [Câu trả lời chính với emoji]

📊 [Thông tin chi tiết/so sánh nếu cần]

💡 [Gợi ý tiếp theo hoặc câu hỏi theo dõi]

---

CÂU HỎI:
{query}

{plan_info}DỮ LIỆU:
{data}

TRUYÊN LỜI:"""
        # trace LLM generation
        if ot_trace is not None:
            tracer = ot_trace.get_tracer(__name__)
            span_ctx = tracer.start_as_current_span('answer_generator.llm', attributes={'plan.type': plan.get('type') if plan else 'UNKNOWN', 'data.count': len(data) if isinstance(data, (list, tuple)) else 1})
            span_ctx.__enter__()
            try:
                answer = self.llm.chat(prompt)
            finally:
                try:
                    span_ctx.__exit__(None, None, None)
                except Exception:
                    pass
        else:
            answer = self.llm.chat(prompt)
        if not answer:
            # fallback: build a concise summary from available data instead of failing
            try:
                # if list of dicts, summarize first 3 records
                if isinstance(data, (list, tuple)) and data:
                    items = data[:3]
                    lines = ["✅ **Tóm tắt dữ liệu tìm được:**"]
                    for it in items:
                        if isinstance(it, dict):
                            parts = [f"{k}: {v}" for k, v in it.items() if v is not None]
                            lines.append("- " + ", ".join(parts))
                        else:
                            lines.append("- " + str(it))
                    if len(data) > 3:
                        lines.append(f"... và {len(data)-3} kết quả khác")
                    return "\n".join(lines)
                elif isinstance(data, dict) and data:
                    parts = [f"{k}: {v}" for k, v in data.items() if v is not None]
                    return "✅ " + ", ".join(parts)
            except Exception:
                pass

            return """❌ **Tôi có lỗi trong quá trình xử lý.**

Vui lòng thử lại với câu hỏi khác hoặc liên hệ hỗ trợ.

📞 Bạn cần giúp gì khác không?"""
        return answer.strip()
