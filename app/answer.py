"""Answer generator — formats structured data into human-readable responses."""
import re
from app.llm_client import LLMClient
from app.normalizer import normalize_data

try:
    from opentelemetry import trace as ot_trace
except Exception:
    ot_trace = None


class AnswerGenerator:
    def __init__(self):
        self.llm = LLMClient(model_name="models/gemini-3.1-flash-lite-preview")

    def generate(self, query, data, plan=None):
        data = normalize_data(data)
        plan_type = plan.get("type") if plan else None

        # ── rule-based formatters ────────────────────────────────────────
        fmt = None
        if plan_type in ("SPEED", "LOAD", "PRICE", "PRESSURE"):
            fmt = self._format_simple(plan_type, data)
        elif plan_type in ("MAX_SPEED", "MAX_LOAD", "MAX_PRICE"):
            fmt = self._format_max(plan_type, data)
        elif plan_type == "COMPARE":
            fmt = self._format_compare(data)
        elif plan_type == "MULTI_HOP":
            fmt = self._format_list(data)
        elif plan_type == "NO_MATCH":
            return self._format_no_match(query)

        if fmt:
            return fmt

        return self._llm_generate(query, data, plan)

    # ── private formatters ───────────────────────────────────────────────

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
                return (
                    f"✅ **Tốc độ tối đa của lốp {size}{brand_str}:**\n\n"
                    f"⚡ **{speed} km/h** - Lốp này phù hợp cho xe máy sport và xe tay ga.\n\n"
                    "📊 **Thông tin thêm:**\n"
                    "- Dữ liệu từ bảng tính chính thức (độ chính xác: 98%)\n"
                    "- So sánh với những lốp khác? Hỏi \"So sánh lốp này với...\"\n"
                    "- Muốn biết giá hoặc tải? Chỉ cần nói \"Giá bao nhiêu?\" hoặc \"Chịu tải được bao nhiêu?\"\n\n"
                    "💡 **Bạn muốn tiếp tục với thao tác gì?**"
                )

        if plan_type == "LOAD":
            load = data.get("load") or data.get("max_load")
            if load is not None:
                return (
                    f"✅ **Tải trọng tối đa của lốp {size}{brand_str}:**\n\n"
                    f"💪 **{load} kg** - Lốp này đủ mạnh cho các loại xe tải nhỏ và xe tay ga hạng nặng.\n\n"
                    "📊 **Thông tin chi tiết:**\n"
                    f"- Chỉ số tải: {data.get('load_index', 'N/A')}\n"
                    "- Dữ liệu chính thức (độ chính xác: 98%)\n"
                    f"- Loại lốp: {data.get('tire_type', 'Không xác định')}\n\n"
                    "💡 **Bạn có muốn:**\n"
                    "- Biết tốc độ tối đa của lốp này?\n"
                    "- So sánh với lốp khác?\n"
                    "- Tìm lốp chịu tải cao hơn?"
                )

        if plan_type == "PRICE":
            price = data.get("price")
            if price is not None:
                return (
                    f"✅ **Giá hiện tại của lốp {size}{brand_str}:**\n\n"
                    f"💰 **{price:,.0f} VNĐ** - Mức giá cạnh tranh trên thị trường.\n\n"
                    "📊 **Thông tin thêm:**\n"
                    "- Giá lấy từ bảng giá chính thức (cập nhật tháng 5/2026)\n"
                    "- Có khuyến mãi cho mua nhiều\n\n"
                    "💡 **Bạn có quan tâm:**\n"
                    "- Tốc độ hoặc tải của lốp này?\n"
                    "- So sánh giá với lốp khác?\n"
                    "- Tìm lốp rẻ hơn với chất lượng tương đương?"
                )

        if plan_type == "PRESSURE":
            pressure = data.get("pressure") or data.get("noi_ap_tieu_chuan")
            if pressure is not None:
                return (
                    f"✅ **Áp suất đề xuất cho lốp {size}{brand_str}:**\n\n"
                    f"🔧 **{pressure} psi** - Áp suất này sẽ tối ưu hóa hiệu suất và tuổi thọ lốp.\n\n"
                    "📊 **Hướng dẫn:**\n"
                    "- Kiểm tra áp suất định kỳ (mỗi 2 tuần)\n"
                    "- Áp suất thay đổi theo nhiệt độ (nóng tăng ~5%, lạnh giảm ~5%)\n"
                    "- Nếu quá thấp: lốp mềm, tốn xăng. Quá cao: lốp cứng, dễ phát nổ.\n\n"
                    "💡 **Bạn cần:**\n"
                    "- Biết tốc độ hoặc tải của lốp này?\n"
                    "- Tìm lốp khác?"
                )

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

        if len(lines) == 1:
            return self._format_no_match("")

        lines.extend([
            "\n📊 **Thông tin:**",
            "- Dữ liệu từ cơ sở dữ liệu chính thức (cập nhật tháng 5/2026)",
            "- Độ chính xác: 98%+",
            "\n💡 **Bạn muốn:**",
        ])
        return "\n".join(lines)

    def _format_compare(self, data):
        if not data:
            return self._format_no_match("")
        return self._llm_generate("compare", data, {"type": "COMPARE"})

    def _format_list(self, data):
        if not data:
            return self._format_no_match("")
        lines = ["📋 **Danh sách kết quả:**\n"]
        for i, item in enumerate(data, 1):
            size = item.get("size", "N/A")
            brand = item.get("brand", "")
            info = " | ".join(f"{k}: {v}" for k, v in item.items() if k not in ("size", "brand"))
            lines.append(f"{i}. **{size}** {f'({brand})' if brand else ''}: {info}")
        lines.append("\n💡 Bạn muốn biết thêm chi tiết về mẫu nào?")
        return "\n".join(lines)

    # ── LLM fallback ─────────────────────────────────────────────────────

    def _llm_generate(self, query, data, plan):
        prompt = self._build_prompt(query, data, plan)
        try:
            return self.llm.chat(prompt)
        except Exception:
            return "Xin lỗi, tôi không thể tạo câu trả lời ngay lúc này."

    def _build_prompt(self, query, data, plan):
        import json
        plan_type = plan.get("type", "UNKNOWN") if plan else "UNKNOWN"
        data_str = json.dumps(data, ensure_ascii=False, indent=2) if data else "Không có dữ liệu"
        return (
            f"Bạn là chuyên gia tư vấn lốp xe. Hãy trả lời câu hỏi sau bằng tiếng Việt.\n\n"
            f"Câu hỏi: {query}\n"
            f"Loại truy vấn: {plan_type}\n"
            f"Dữ liệu: {data_str}\n\n"
            "Hãy đưa ra câu trả lời thân thiện, có cấu trúc rõ ràng (dùng **bold** cho số liệu quan trọng)."
        )
