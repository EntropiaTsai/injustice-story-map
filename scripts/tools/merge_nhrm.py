"""
合併 NHRM 爬蟲結果與 twtjdb 資料，輸出地圖用的 JSON。

以 NHRM 記錄為主（12,060 筆），透過 twtjdb_ids 連結 twtjdb 資料取得
判決詳情與座標。找不到座標的，依下列優先順序嘗試 geocode：
  1. twtjdb 已有座標（被捕前居住地，最可靠）
  2. NHRM city 欄位（若省份為臺灣）
  3. NHRM introduction 文字擷取縣市名
  4. twtjdb native_province/native_city（籍貫，最後手段）

輸出：
  data/processed/nhrm_merged.json    全部 12,060 筆
  public/data/nhrm_map_ready.json    僅有座標的筆數（供網頁使用）

用法：
  python merge_nhrm.py
  python merge_nhrm.py --nhrm data/raw/nhrm_all.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]

# ── 台灣縣市座標（與 process_twtjdb.py 共用同一份對照表）─────────────────────
TAIWAN_LOCATIONS: dict[str, tuple[float, float]] = {
    "台北市": (25.0330, 121.5654), "臺北市": (25.0330, 121.5654),
    "新北市": (25.0120, 121.4651),
    "桃園市": (24.9937, 121.3010),
    "台中市": (24.1477, 120.6736), "臺中市": (24.1477, 120.6736),
    "台南市": (22.9999, 120.2270), "臺南市": (22.9999, 120.2270),
    "高雄市": (22.6273, 120.3014),
    "基隆市": (25.1276, 121.7392),
    "新竹市": (24.8066, 120.9686),
    "嘉義市": (23.4801, 120.4491),
    "宜蘭縣": (24.7021, 121.7378),
    "新竹縣": (24.8387, 121.0177),
    "苗栗縣": (24.5602, 120.8214),
    "彰化縣": (24.0684, 120.5820),
    "南投縣": (23.9609, 120.9718),
    "雲林縣": (23.7092, 120.4313),
    "嘉義縣": (23.4518, 120.2554),
    "屏東縣": (22.5519, 120.5487),
    "台東縣": (22.7972, 121.0713), "臺東縣": (22.7972, 121.0713),
    "花蓮縣": (23.9872, 121.6015),
    "澎湖縣": (23.5711, 119.5795),
    "金門縣": (24.4493, 118.3767),
    "連江縣": (26.1505, 119.9289),
    "台北縣": (25.0120, 121.4651), "臺北縣": (25.0120, 121.4651),
    "高雄縣": (22.6273, 120.3014),
    "台南縣": (22.9999, 120.2270), "臺南縣": (22.9999, 120.2270),
    "桃園縣": (24.9937, 121.3010),
    "台中縣": (24.1477, 120.6736), "臺中縣": (24.1477, 120.6736),
    "台灣省": (23.6978, 120.9605), "臺灣省": (23.6978, 120.9605),
    "綠島":   (22.6607, 121.4920),
    "火燒島": (22.6607, 121.4920),
}


CHINESE_NUMS: dict[str, int] = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
    '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20,
}


def derive_penalty_level(judgment: dict | None, nhrm_penalty: list) -> str:
    """從 twtjdb 判決或 NHRM 刑罰欄位推導刑罰等級。"""
    # 優先用 twtjdb 結構化欄位
    if judgment:
        if judgment.get("has_death_penalty") or judgment.get("has_life_sentence"):
            return "death"
        text = str(judgment.get("penalty_text") or "")
        if "死刑" in text:
            return "death"
        arabic = [int(m) for m in re.findall(r"有期徒刑(\d+)年", text)]
        chinese = [v for k, v in CHINESE_NUMS.items() if f"有期徒刑{k}年" in text]
        years = arabic + chinese
        if years:
            return "heavy" if max(years) >= 10 else "light"

    # fallback：NHRM penalty term
    for p in (nhrm_penalty or []):
        term = (p.get("term") or "") + (p.get("penalty_text") or "")
        if "死刑" in term or "無期" in term:
            return "death"
        arabic = [int(m) for m in re.findall(r"(\d+)年", term)]
        chinese = [v for k, v in CHINESE_NUMS.items() if f"{k}年" in term]
        years = arabic + chinese
        if years:
            return "heavy" if max(years) >= 10 else "light"

    return "unknown"


def geocode(text: str | None) -> tuple[float, float] | None:
    if not text:
        return None
    for key, coords in TAIWAN_LOCATIONS.items():
        if key in text:
            return coords
    return None


def extract_location_from_intro(text: str | None) -> str | None:
    """從傳記文字中擷取縣市地名。"""
    if not text:
        return None
    # 「○○縣人」「○○市人」「○○縣○○人」
    patterns = [
        r"([台臺][灣]?[^\s，。、（）\d]{0,4}(?:縣|市))人",
        r"住([台臺]?灣?[省]?[^\s，。、（）\d]{2,6}(?:縣|市))",
        r"([台臺][灣]?[^\s，。、（）\d]{0,4}(?:縣|市))[^\s，。]{0,5}人",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()
    return None


# ── 載入資料 ───────────────────────────────────────────────────────────────────

def load_twtjdb() -> dict[str, dict]:
    """回傳 {twtjdb_id: person_dict}。"""
    persons: dict[str, dict] = {}
    for fname in ("twtjdb_map_ready.json", "twtjdb_pending.json"):
        with open(REPO / "data/processed" / fname, encoding="utf-8") as f:
            for p in json.load(f)["persons"]:
                persons[str(p["id"])] = p
    return persons


def load_nhrm(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# ── 合併單筆 ───────────────────────────────────────────────────────────────────

def merge_one(nhrm: dict, twtjdb: dict[str, dict]) -> dict[str, Any]:
    # 找第一筆有效的 twtjdb 記錄
    twtjdb_rec: dict | None = None
    twtjdb_id: str | None = None
    for tid in (nhrm.get("twtjdb_ids") or []):
        if tid in twtjdb:
            twtjdb_rec = twtjdb[tid]
            twtjdb_id = tid
            break

    # ── 座標 ──────────────────────────────────────────────────────────────────
    lat = lng = None
    location_source: str | None = None
    location_raw: str | None = None

    # 1. twtjdb 已有座標
    if twtjdb_rec and twtjdb_rec.get("lat"):
        lat = twtjdb_rec["lat"]
        lng = twtjdb_rec["lng"]
        location_raw = twtjdb_rec.get("location_raw")
        location_source = "twtjdb"

    # 2. NHRM city（省份為臺灣時）
    if lat is None:
        province = nhrm.get("province") or ""
        city = nhrm.get("city") or ""
        if "臺灣" in province or "台灣" in province:
            coords = geocode(city)
            if coords:
                lat, lng = coords
                location_raw = city
                location_source = "nhrm_city"

    # 3. introduction 文字擷取
    if lat is None:
        extracted = extract_location_from_intro(nhrm.get("introduction"))
        coords = geocode(extracted)
        if coords:
            lat, lng = coords
            location_raw = extracted
            location_source = "nhrm_intro"

    # 4. twtjdb 籍貫（最後手段）
    if lat is None and twtjdb_rec:
        native = (twtjdb_rec.get("native_province") or "") + (twtjdb_rec.get("native_city") or "")
        coords = geocode(native)
        if coords:
            lat, lng = coords
            location_raw = native
            location_source = "native"

    # ── 判決資料（從 twtjdb 取，較結構化） ───────────────────────────────────
    judgment: dict | None = None
    if twtjdb_rec:
        j = twtjdb_rec.get("judgment") or twtjdb_rec.get("final_judgment") or {}
        judgment = {
            "authority": j.get("authority"),
            "year_roc": j.get("year_roc"),
            "penalty_text": j.get("penalty_text"),
            "has_death_penalty": j.get("has_death_penalty", False),
            "has_life_sentence": j.get("has_life_sentence", False),
            "organization": j.get("organization"),
        }

    nhrm_penalty = nhrm.get("penalty") or []
    penalty_level = derive_penalty_level(judgment, nhrm_penalty)

    return {
        "nhrm_id": nhrm["nhrm_id"],
        "twtjdb_id": twtjdb_id,
        "name": nhrm.get("name"),
        "nickname": nhrm.get("nickname"),
        "gender": nhrm.get("gender"),
        "birth_year": nhrm.get("birth_year"),
        "death_year": nhrm.get("death_year"),
        "province": nhrm.get("province"),
        "city": nhrm.get("city"),
        "place": nhrm.get("place"),
        "lat": lat,
        "lng": lng,
        "location_source": location_source,
        "location_raw": location_raw,
        "penalty_level": penalty_level,
        "image_url": nhrm.get("image_url"),
        "introduction": nhrm.get("introduction"),
        "nhrm_url": nhrm.get("url"),
        "judgment": judgment,
        "nhrm_penalty": nhrm_penalty,
        "cases": nhrm.get("cases") or [],
        "related_persons": nhrm.get("related_persons") or [],
        "recoup": nhrm.get("recoup") or [],
        "documents": nhrm.get("documents") or [],
    }


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main(nhrm_path: Path, output_path: Path) -> None:
    print("載入 twtjdb...", file=sys.stderr)
    twtjdb = load_twtjdb()
    print(f"  {len(twtjdb)} 筆", file=sys.stderr)

    print(f"載入 NHRM ({nhrm_path.name})...", file=sys.stderr)
    nhrm_records = load_nhrm(nhrm_path)
    valid = [r for r in nhrm_records if not r.get("error")]
    print(f"  {len(nhrm_records)} 筆（有效 {len(valid)} 筆）", file=sys.stderr)

    persons = []
    stats: dict[str, int] = {
        "with_coords": 0,
        "no_coords": 0,
        "source_twtjdb": 0,
        "source_nhrm_city": 0,
        "source_nhrm_intro": 0,
        "source_native": 0,
        "has_twtjdb_match": 0,
        "no_twtjdb_match": 0,
    }

    for rec in valid:
        merged = merge_one(rec, twtjdb)
        persons.append(merged)

        if merged["lat"] is not None:
            stats["with_coords"] += 1
            stats[f"source_{merged['location_source']}"] += 1
        else:
            stats["no_coords"] += 1

        if merged["twtjdb_id"]:
            stats["has_twtjdb_match"] += 1
        else:
            stats["no_twtjdb_match"] += 1

    meta = {"nhrm_total": len(nhrm_records), "valid": len(valid), **stats}
    output = {"_meta": meta, "persons": persons}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 供網頁使用：只保留有座標的筆數
    public_path = REPO / "public" / "data" / "nhrm_map_ready.json"
    public_path.parent.mkdir(parents=True, exist_ok=True)
    map_ready = [p for p in persons if p["lat"] is not None]
    with open(public_path, "w", encoding="utf-8") as f:
        json.dump({"_meta": {**meta, "map_ready": len(map_ready)}, "persons": map_ready},
                  f, ensure_ascii=False)  # 不縮排，節省檔案大小

    print(f"\n完成 → {output_path}", file=sys.stderr)
    print(f"       → {public_path} ({len(map_ready)} 筆)", file=sys.stderr)
    print(f"  有座標：{stats['with_coords']} 筆", file=sys.stderr)
    print(f"    來源 twtjdb：{stats['source_twtjdb']}", file=sys.stderr)
    print(f"    來源 NHRM city：{stats['source_nhrm_city']}", file=sys.stderr)
    print(f"    來源 introduction：{stats['source_nhrm_intro']}", file=sys.stderr)
    print(f"    來源 native：{stats['source_native']}", file=sys.stderr)
    print(f"  無座標：{stats['no_coords']} 筆", file=sys.stderr)
    print(f"  有 twtjdb 對應：{stats['has_twtjdb_match']} 筆", file=sys.stderr)
    print(f"  無 twtjdb 對應：{stats['no_twtjdb_match']} 筆", file=sys.stderr)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--nhrm",
        default=str(REPO / "data/raw/nhrm_all.jsonl"),
        help="NHRM 爬蟲輸出 JSONL（預設：data/raw/nhrm_all.jsonl）",
    )
    parser.add_argument(
        "--out",
        default=str(REPO / "data/processed/nhrm_merged.json"),
        help="輸出 JSON（預設：data/processed/nhrm_merged.json）",
    )
    args = parser.parse_args()
    main(Path(args.nhrm), Path(args.out))
