"""
用 Gemini 替 nhrm_merged.json 中無座標記錄推斷案發地點，輸出 patch 檔。

用法：
  python nhrm_geocode_llm.py --key YOUR_API_KEY
  python nhrm_geocode_llm.py --key YOUR_API_KEY --batch 50 --delay 1.0

輸出：
  data/processed/nhrm_llm_patch.jsonl   每行 {"nhrm_id": N, "location_raw": "...", "lat": ..., "lng": ...}

之後執行 merge_nhrm.py 時會自動讀取這份 patch（若存在）。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

REPO = Path(__file__).resolve().parents[2]

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
    "綠島":   (22.6607, 121.4920), "火燒島": (22.6607, 121.4920),
    "內湖":   (25.0630, 121.5939),
    "景美":   (24.9984, 121.5415),
    "新店":   (24.9716, 121.5378),
    "板橋":   (25.0141, 121.4617),
    "淡水":   (25.1711, 121.4497),
    "三重":   (25.0620, 121.4924),
    "中和":   (24.9999, 121.4889),
    "永和":   (25.0133, 121.5195),
    "台北":   (25.0330, 121.5654), "臺北": (25.0330, 121.5654),
    "北市":   (25.0330, 121.5654),
    "基隆":   (25.1276, 121.7392),
    "桃園":   (24.9937, 121.3010),
    "新竹":   (24.8066, 120.9686),
    "苗栗":   (24.5602, 120.8214),
    "竹南":   (24.6874, 120.8639),
    "中壢":   (24.9636, 121.2249),
    "台中":   (24.1477, 120.6736), "臺中": (24.1477, 120.6736),
    "豐原":   (24.2537, 120.7196),
    "清水":   (24.3636, 120.5638),
    "土城":   (24.9750, 121.4378),
    "彰化":   (24.0684, 120.5820),
    "員林":   (23.9586, 120.5710),
    "南投":   (23.9609, 120.9718),
    "埔里":   (23.9611, 120.9735),
    "雲林":   (23.7092, 120.4313),
    "斗六":   (23.7104, 120.5428),
    "虎尾":   (23.7082, 120.4394),
    "嘉義":   (23.4801, 120.4491),
    "台南":   (22.9999, 120.2270), "臺南": (22.9999, 120.2270),
    "新營":   (23.3116, 120.3123),
    "善化":   (23.1434, 120.2977),
    "歸仁":   (22.9654, 120.2914),
    "高雄":   (22.6273, 120.3014),
    "岡山":   (22.7953, 120.2949),
    "鳳山":   (22.6271, 120.3567),
    "旗山":   (22.8878, 120.4806),
    "左營":   (22.6911, 120.2954),
    "屏東":   (22.5519, 120.5487),
    "澎湖":   (23.5711, 119.5795),
    "馬公":   (23.5642, 119.5631),
    "花蓮":   (23.9872, 121.6015),
    "玉里":   (23.6327, 121.3149),
    "台東":   (22.7972, 121.0713), "臺東": (22.7972, 121.0713),
    "泰源":   (23.1167, 121.2500),
    "宜蘭":   (24.7021, 121.7378),
    "羅東":   (24.6776, 121.7712),
    "漁翁島": (23.6000, 119.5000),
    "臺灣大學": (25.0174, 121.5396), "台灣大學": (25.0174, 121.5396),
    "馬場町": (25.0302, 121.5057),
    "六張犁": (25.0244, 121.5607),
    "士林":   (25.0878, 121.5240),
    "北投":   (25.1317, 121.4989),
    "木柵":   (24.9983, 121.5681),
    "萬華":   (25.0374, 121.5000),
    "大稻埕": (25.0568, 121.5108),
    "汐止":   (25.0698, 121.6604),
    "金瓜石": (25.1093, 121.8525),
    "蘇澳":   (24.5978, 121.8438),
    "頭城":   (24.8460, 121.8188),
    "台東市": (22.7972, 121.0713), "臺東市": (22.7972, 121.0713),
    "關山":   (23.0528, 121.1672),
    "池上":   (23.1089, 121.2233),
    "成功":   (23.0994, 121.3706),
}

SYSTEM_PROMPT = """\
你是一個專門處理台灣白色恐怖史料的地名抽取助手。
我會給你多位受難者的傳記片段，格式為 JSON 陣列，每個元素有 id 和 text 欄位。
請回傳一個 JSON 陣列，每個元素格式為 {"id": N, "location": "地名或null"}。
地名請選台灣境內的縣、市、鄉、鎮或設施名（如「高雄市」「綠島」「鳳山」「泰源」「景美」「岡山」等）。
若某筆找不到台灣地名，該筆 location 填 null。
只回傳 JSON 陣列，不要其他說明。"""


def geocode(name: str | None) -> tuple[float, float] | None:
    if not name:
        return None
    sorted_keys = sorted(TAIWAN_LOCATIONS.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in name:
            return TAIWAN_LOCATIONS[key]
    return None


def ask_gemini_batch(
    client: genai.Client,
    items: list[dict],  # [{"id": nhrm_id, "text": intro[:150]}, ...]
    retries: int = 6,
) -> dict[int, str | None]:
    """送一批記錄給 Gemini，回傳 {nhrm_id: location_name_or_None}。"""
    import re as _re

    prompt = json.dumps(items, ensure_ascii=False)

    for attempt in range(retries):
        try:
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0,
                    max_output_tokens=256,
                ),
            )
            raw = (resp.text or "").strip()
            # 移除 markdown code fence（如果有）
            raw = _re.sub(r'^```(?:json)?\s*', '', raw)
            raw = _re.sub(r'\s*```$', '', raw)
            parsed = json.loads(raw)
            result: dict[int, str | None] = {}
            for entry in parsed:
                loc = entry.get("location")
                if loc and loc.lower() != "null" and loc not in ("無", "不明"):
                    result[int(entry["id"])] = loc
                else:
                    result[int(entry["id"])] = None
            return result
        except Exception as e:
            msg = str(e)
            m = _re.search(r'retry[^0-9]*(\d+(?:\.\d+)?)s', msg, _re.IGNORECASE)
            wait = min(int(float(m.group(1))) + 3, 120) if m else min(20 * (attempt + 1), 120)
            if attempt < retries - 1 and ("429" in msg or "RESOURCE_EXHAUSTED" in msg):
                print(f"    rate limit，等待 {wait}s 後重試...", file=sys.stderr)
                time.sleep(wait)
            elif attempt < retries - 1:
                # JSON parse 失敗等情況，短暫等待後重試
                print(f"    解析失敗（{msg[:80]}），等待 5s 重試...", file=sys.stderr)
                time.sleep(5)
            else:
                # 全部重試失敗，回傳全 None
                print(f"    批次失敗，跳過此批：{msg[:120]}", file=sys.stderr)
                return {int(item["id"]): None for item in items}
    return {int(item["id"]): None for item in items}


def load_done(patch_path: Path) -> dict[int, dict]:
    done: dict[int, dict] = {}
    if patch_path.exists():
        with open(patch_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    obj = json.loads(line)
                    done[obj["nhrm_id"]] = obj
    return done


def load_env_file() -> None:
    """讀取 repo 根目錄的 .env，把 KEY=VALUE 載入 os.environ（不覆蓋已有值）。"""
    env_path = REPO / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


def main() -> None:
    load_env_file()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--key",
        default=os.environ.get("GEMINI_API_KEY", ""),
        help="Gemini API key（也可設 GEMINI_API_KEY 環境變數或寫進 .env）",
    )
    parser.add_argument(
        "--input",
        default=str(REPO / "data/processed/nhrm_merged.json"),
        help="nhrm_merged.json 路徑",
    )
    parser.add_argument(
        "--out",
        default=str(REPO / "data/processed/nhrm_llm_patch.jsonl"),
        help="輸出 patch JSONL",
    )
    parser.add_argument("--delay", type=float, default=13.0, help="每次 API 請求間隔秒數（free tier 限 5 req/min，建議 ≥13）")
    parser.add_argument("--batch-size", type=int, default=5, help="每次 API 呼叫包含幾筆（預設 5）")
    parser.add_argument("--limit", type=int, default=0, help="最多處理幾筆記錄（0=全部）")
    args = parser.parse_args()

    api_key = args.key.strip()
    if not api_key:
        print("錯誤：請提供 Gemini API key（--key 參數、GEMINI_API_KEY 環境變數，或 .env 檔案）", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    patch_path = Path(args.out)

    print("載入 nhrm_merged.json...", file=sys.stderr)
    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    persons = data["persons"]

    no_coord = [p for p in persons if p.get("lat") is None]
    print(f"  無座標筆數：{len(no_coord)}", file=sys.stderr)

    done = load_done(patch_path)
    print(f"  已處理（從 patch 載入）：{len(done)} 筆", file=sys.stderr)

    pending = [p for p in no_coord if p["nhrm_id"] not in done]
    if args.limit > 0:
        pending = pending[: args.limit]
    print(f"  待處理：{len(pending)} 筆（每批 {args.batch_size} 筆）", file=sys.stderr)

    hit = 0
    miss = 0
    processed = 0

    bs = args.batch_size
    with open(patch_path, "a", encoding="utf-8") as out_f:
        for batch_start in range(0, len(pending), bs):
            chunk = pending[batch_start: batch_start + bs]

            # 無傳記文字的直接跳過，不送 API
            no_text = [p for p in chunk if not (p.get("introduction") or "").strip()]
            has_text = [p for p in chunk if (p.get("introduction") or "").strip()]

            for p in no_text:
                record = {"nhrm_id": p["nhrm_id"], "location_raw": None, "lat": None, "lng": None}
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                miss += 1

            if has_text:
                items = [
                    {"id": p["nhrm_id"], "text": (p.get("introduction") or "")[:150]}
                    for p in has_text
                ]
                results = ask_gemini_batch(client, items)

                for p in has_text:
                    location_name = results.get(p["nhrm_id"])
                    coords = geocode(location_name)
                    if coords:
                        lat, lng = coords
                        record = {"nhrm_id": p["nhrm_id"], "location_raw": location_name, "lat": lat, "lng": lng}
                        hit += 1
                    else:
                        record = {"nhrm_id": p["nhrm_id"], "location_raw": location_name, "lat": None, "lng": None}
                        miss += 1
                    out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

                out_f.flush()

            processed += len(chunk)
            if processed % (bs * 10) == 0 or processed >= len(pending):
                print(
                    f"  [{processed}/{len(pending)}] hit={hit} miss={miss}",
                    file=sys.stderr,
                )

            if batch_start + bs < len(pending):
                time.sleep(args.delay)

    total_hit = sum(1 for v in done.values() if v.get("lat") is not None) + hit
    print(f"\n完成。本次新增有座標：{hit}，無法定位：{miss}", file=sys.stderr)
    print(f"patch 檔累計有座標：{total_hit} 筆 → {patch_path}", file=sys.stderr)
    print("請再執行 merge_nhrm.py 套用 patch。", file=sys.stderr)


if __name__ == "__main__":
    main()
