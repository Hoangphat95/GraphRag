def normalize_record(rec: dict) -> dict:
    if not isinstance(rec, dict):
        return rec
    nr = dict(rec)
    # canonical aliases
    nr['max_speed'] = nr.get('max_speed') or nr.get('toc_do_toi_da') or nr.get('speed')
    nr['max_load'] = nr.get('max_load') or nr.get('tai_trong_lon_nhat') or nr.get('load')
    nr['price'] = nr.get('price') or nr.get('gia_ban_co_vat') or nr.get('gia_ban')
    # consumer-friendly fallbacks
    nr['speed'] = nr.get('speed') or nr.get('max_speed') or nr.get('toc_do_toi_da')
    nr['load'] = nr.get('load') or nr.get('max_load') or nr.get('tai_trong_lon_nhat')
    return nr


def normalize_data(data):
    if data is None:
        return data
    if isinstance(data, dict):
        return normalize_record(data)
    if isinstance(data, list):
        return [normalize_record(d) if isinstance(d, dict) else d for d in data]
    return data
