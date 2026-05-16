class ResultReasoner:

    def reason(self, query, data, plan_type=None):

        # =========================
        # NO-MATCH (AMBIGUOUS)
        # =========================
        if plan_type == "NO_MATCH":
            return {
                "type": "AMBIGUOUS",
                "message": (
                    "Mình cần thêm thông tin để tư vấn chính xác hơn.\n"
                    "Vui lòng cho biết thêm:\n"
                    "- kích thước lốp (ví dụ: 120/70-17)\n"
                    "- thương hiệu lốp (ví dụ: DPLUS, IRC, MAXXIS)\n"
                    "- tiêu chí bạn muốn tối ưu (tốc độ, chịu tải, giá, độ bền...)\n"
                )
            }

        if not data:
            return None

        first = data[0]
        has_many = len(data) > 1

        # =========================
        # COMPARE
        # =========================
        if plan_type == "COMPARE":
            return {
                "type": "COMPARE",
                "data": self._compare(data)
            }

        # =========================
        # MAX LOAD
        # =========================
        if plan_type == "MAX_LOAD":
            return {
                "type": "MAX_LOAD",
                "data": data   # 🔥 giữ full list
            }

        # =========================
        # MAX SPEED
        # =========================
        if plan_type == "MAX_SPEED":
            return {
                "type": "MAX_SPEED",
                "data": data   # 🔥 giữ full list
            }

        # =========================
        # MAX PRICE
        # =========================
        if plan_type == "MAX_PRICE":
            return {
                "type": "MAX_PRICE",
                "data": data
            }

        # =========================
        # LOAD (SMART)
        # =========================
        if plan_type == "LOAD":

            # ❌ không có size → hỏi lại
            if not first.get("size"):
                return {
                    "type": "ASK_SIZE",
                    "message": "Bạn vui lòng cung cấp kích thước lốp (ví dụ: 120/70-17) để tôi kiểm tra chính xác."
                }

            return {
                "type": "LOAD",
                "data": {
                    "size": first.get("size"),
                    "load": first.get("load")
                }
            }

        # =========================
        # SPEED
        # =========================
        if plan_type == "SPEED":
            return {
                "type": "SPEED",
                "data": {
                    "size": first.get("size"),
                    "brand": first.get("brand"),
                    "speed": first.get("speed")
                }
            }

        # =========================
        # PRICE
        # =========================
        if plan_type == "PRICE":
            return {
                "type": "PRICE",
                "data": {
                    "size": first.get("size"),
                    "price": first.get("price")
                }
            }

        # =========================
        # PRESSURE
        # =========================
        if plan_type == "PRESSURE":
            return {
                "type": "PRESSURE",
                "data": {
                    "size": first.get("size"),
                    "pressure": first.get("pressure")
                }
            }

        # =========================
        # NO-MATCH (AMBIGUOUS)
        # =========================
        if plan_type == "NO_MATCH":
            return {
                "type": "AMBIGUOUS",
                "message": (
                    "Mình cần thêm thông tin để tư vấn chính xác hơn.\n"
                    "Vui lòng cho biết thêm:\n"
                    "- kích thước lốp (ví dụ: 120/70-17)\n"
                    "- thương hiệu lốp (ví dụ: DPLUS, IRC, MAXXIS)\n"
                    "- tiêu chí bạn muốn tối ưu (tốc độ, chịu tải, giá, độ bền...)\n"
                )
            }

        # =========================
        # DEFAULT
        # =========================
        return {
            "type": "FULL",
            "data": first
        }

    # =========================
    # COMPARE FORMAT
    # =========================
    def _compare(self, data):
        # Return structured records for compare so downstream formatters
        # receive consistent dicts instead of free-form strings.
        preferred_keys = ["size", "brand", "load", "speed", "pressure", "diameter", "rim", "structure", "pattern", "price", "gia_ban_co_vat"]

        results = []
        seen_sizes = set()

        for row in data:
            size = row.get('size') or row.get('muc_kich_thuoc') or 'unknown'
            if size in seen_sizes:
                # merge duplicates: prefer non-null numeric values and extend patterns
                for r in results:
                    if r.get('size') == size:
                        # merge fields
                        for k in preferred_keys:
                            v_new = row.get(k)
                            v_old = r.get(k)
                            if v_new is None:
                                continue
                            if k == 'pattern':
                                # normalize to list
                                if isinstance(v_new, list):
                                    new_list = v_new
                                else:
                                    new_list = [x.strip() for x in str(v_new).split(',') if x.strip()]
                                old_list = r.get('pattern') or []
                                r['pattern'] = list(dict.fromkeys(old_list + new_list))
                            else:
                                # choose max for numeric-like fields, else prefer existing
                                try:
                                    if isinstance(v_new, (int, float)) and isinstance(v_old, (int, float)):
                                        r[k] = max(v_old, v_new)
                                    elif v_old in (None, ''):
                                        r[k] = v_new
                                except Exception:
                                    if not r.get(k):
                                        r[k] = v_new
                        break
                continue

            rec = {}
            rec['size'] = size
            if row.get('brand'):
                rec['brand'] = row.get('brand')

            for k in preferred_keys:
                if k in row and row.get(k) is not None:
                    rec[k] = row.get(k)

            # include other keys as-is
            for k, v in row.items():
                if k not in rec and v is not None:
                    rec[k] = v

            results.append(rec)
            seen_sizes.add(size)

        return results