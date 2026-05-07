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
    # ── 直轄市、縣市 ──────────────────────────────────────────────────────────
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
    # ── 離島 ─────────────────────────────────────────────────────────────────
    "綠島":   (22.6607, 121.4920),
    "火燒島": (22.6607, 121.4920),
    # ── 區/鎮/設施（映射到最近縣市中心）──────────────────────────────────────
    # 台北市內行政區與設施
    "內湖":   (25.0630, 121.5939),   # 台北市內湖區（含內湖新生總隊）
    "景美":   (24.9984, 121.5415),   # 台北市文山區景美（景美看守所/軍法處）
    "新店":   (24.9716, 121.5378),   # 新北市新店（安坑彈藥庫）
    "板橋":   (25.0141, 121.4617),   # 新北市板橋
    "淡水":   (25.1711, 121.4497),   # 新北市淡水
    "三重":   (25.0620, 121.4924),   # 新北市三重
    "中和":   (24.9999, 121.4889),   # 新北市中和
    "永和":   (25.0133, 121.5195),   # 新北市永和
    # 台北（非市）泛稱
    "台北":   (25.0330, 121.5654),   # 泛台北地區
    "臺北":   (25.0330, 121.5654),
    "北市":   (25.0330, 121.5654),
    # 基隆
    "基隆":   (25.1276, 121.7392),
    # 桃竹苗
    "桃園":   (24.9937, 121.3010),
    "新竹":   (24.8066, 120.9686),
    "苗栗":   (24.5602, 120.8214),
    "竹南":   (24.6874, 120.8639),
    "中壢":   (24.9636, 121.2249),   # 桃園市中壢
    # 台中
    "台中":   (24.1477, 120.6736),
    "臺中":   (24.1477, 120.6736),
    "豐原":   (24.2537, 120.7196),   # 台中市豐原
    "清水":   (24.3636, 120.5638),   # 台中市清水（注意：土城清水是台中）
    "土城":   (24.9750, 121.4378),   # 新北市土城（土城清水即台中清水，但 place 多指土城看守所→新北）
    # 彰化
    "彰化":   (24.0684, 120.5820),
    "員林":   (23.9586, 120.5710),   # 彰化縣員林
    # 南投
    "南投":   (23.9609, 120.9718),
    "埔里":   (23.9611, 120.9735),
    # 雲林
    "雲林":   (23.7092, 120.4313),
    "斗六":   (23.7104, 120.5428),
    "虎尾":   (23.7082, 120.4394),
    # 嘉義
    "嘉義":   (23.4801, 120.4491),
    # 台南
    "台南":   (22.9999, 120.2270),
    "臺南":   (22.9999, 120.2270),
    "新營":   (23.3116, 120.3123),   # 台南市新營
    "善化":   (23.1434, 120.2977),
    "歸仁":   (22.9654, 120.2914),
    # 高雄
    "高雄":   (22.6273, 120.3014),
    "岡山":   (22.7953, 120.2949),   # 高雄市岡山（空軍岡山基地）
    "鳳山":   (22.6271, 120.3567),   # 高雄市鳳山（鳳山招待所）
    "旗山":   (22.8878, 120.4806),   # 高雄市旗山
    "左營":   (22.6911, 120.2954),   # 高雄市左營（海軍）
    "屏東":   (22.5519, 120.5487),
    # 澎湖
    "澎湖":   (23.5711, 119.5795),   # 澎湖縣（含澎湖新生隊）
    "馬公":   (23.5642, 119.5631),   # 澎湖縣馬公
    # 花東
    "花蓮":   (23.9872, 121.6015),
    "玉里":   (23.6327, 121.3149),   # 花蓮縣玉里（玉里榮民醫院關押處）
    "台東":   (22.7972, 121.0713),
    "臺東":   (22.7972, 121.0713),
    "泰源":   (23.1167, 121.2500),   # 台東縣東河（泰源感訓監獄）
    # 宜蘭
    "宜蘭":   (24.7021, 121.7378),
    "羅東":   (24.6776, 121.7712),
    # 常見機構/地點
    "漁翁島": (23.6000, 119.5000),   # 澎湖縣西嶼
    "臺灣大學": (25.0174, 121.5396), "台灣大學": (25.0174, 121.5396),
    "馬場町": (25.0302, 121.5057),   # 台北市萬華（刑場）
    "六張犁": (25.0244, 121.5607),   # 台北市信義（政治犯墓地）
    "士林":   (25.0878, 121.5240),   # 台北市士林
    "北投":   (25.1317, 121.4989),   # 台北市北投
    "木柵":   (24.9983, 121.5681),   # 台北市文山
    "萬華":   (25.0374, 121.5000),   # 台北市萬華
    "大稻埕": (25.0568, 121.5108),   # 台北市大同
    "汐止":   (25.0698, 121.6604),   # 新北市汐止
    "金瓜石": (25.1093, 121.8525),   # 新北市瑞芳（戰俘營）
    "蘇澳":   (24.5978, 121.8438),   # 宜蘭縣蘇澳
    "頭城":   (24.8460, 121.8188),   # 宜蘭縣頭城
    "台東市": (22.7972, 121.0713), "臺東市": (22.7972, 121.0713),
    "關山":   (23.0528, 121.1672),   # 台東縣關山
    "池上":   (23.1089, 121.2233),   # 台東縣池上
    "成功":   (23.0994, 121.3706),   # 台東縣成功
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
    """從傳記文字擷取案發地名。優先掃前 150 字，並優先比對較長（更精確）的地名。"""
    if not text:
        return None
    head = text[:150]
    # 先比對較長的鍵（避免「新竹市」被「新竹」截斷），按長度降序排列
    sorted_keys = sorted(TAIWAN_LOCATIONS.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in head:
            return key
    # fallback：掃全文
    for key in sorted_keys:
        if key in text:
            return key
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

    # 3. NHRM place 欄位（關押地/案發地，如「綠島」「泰源」「鳳山」）
    if lat is None:
        place = nhrm.get("place") or ""
        coords = geocode(place)
        if coords:
            lat, lng = coords
            location_raw = place
            location_source = "nhrm_place"

    # 4. introduction 文字擷取（案發地常在前 150 字）
    if lat is None:
        extracted = extract_location_from_intro(nhrm.get("introduction"))
        coords = geocode(extracted)
        if coords:
            lat, lng = coords
            location_raw = extracted
            location_source = "nhrm_intro"

    # 5. twtjdb 籍貫（最後手段）
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

def load_llm_patch() -> dict[int, dict]:
    """讀取 Gemini geocoding patch，回傳 {nhrm_id: {lat, lng, location_raw}}。"""
    patch_path = REPO / "data/processed/nhrm_llm_patch.jsonl"
    patch: dict[int, dict] = {}
    if not patch_path.exists():
        return patch
    with open(patch_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                obj = json.loads(line)
                nid = obj["nhrm_id"]
                if obj.get("lat") is not None:
                    patch[nid] = obj
    print(f"  LLM patch 有座標：{len(patch)} 筆", file=sys.stderr)
    return patch


def main(nhrm_path: Path, output_path: Path) -> None:
    print("載入 twtjdb...", file=sys.stderr)
    twtjdb = load_twtjdb()
    print(f"  {len(twtjdb)} 筆", file=sys.stderr)

    print(f"載入 NHRM ({nhrm_path.name})...", file=sys.stderr)
    nhrm_records = load_nhrm(nhrm_path)
    valid = [r for r in nhrm_records if not r.get("error")]
    print(f"  {len(nhrm_records)} 筆（有效 {len(valid)} 筆）", file=sys.stderr)

    print("載入 LLM geocoding patch...", file=sys.stderr)
    llm_patch = load_llm_patch()

    persons = []
    stats: dict[str, int] = {
        "with_coords": 0,
        "no_coords": 0,
        "source_twtjdb": 0,
        "source_nhrm_city": 0,
        "source_nhrm_place": 0,
        "source_nhrm_intro": 0,
        "source_native": 0,
        "source_llm": 0,
        "has_twtjdb_match": 0,
        "no_twtjdb_match": 0,
    }

    for rec in valid:
        merged = merge_one(rec, twtjdb)

        # 6. LLM geocoding patch（最後手段，只補無座標記錄）
        if merged["lat"] is None and rec["nhrm_id"] in llm_patch:
            p = llm_patch[rec["nhrm_id"]]
            merged["lat"] = p["lat"]
            merged["lng"] = p["lng"]
            merged["location_raw"] = p["location_raw"]
            merged["location_source"] = "llm"

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
    print(f"    來源 NHRM place：{stats['source_nhrm_place']}", file=sys.stderr)
    print(f"    來源 introduction：{stats['source_nhrm_intro']}", file=sys.stderr)
    print(f"    來源 native：{stats['source_native']}", file=sys.stderr)
    print(f"    來源 LLM (Gemini)：{stats['source_llm']}", file=sys.stderr)
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
