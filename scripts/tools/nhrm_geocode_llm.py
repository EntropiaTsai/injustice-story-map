"""
用 Claude Haiku 替 nhrm_merged.json 中無座標記錄推斷案發地點，輸出 patch 檔。

用法：
  python nhrm_geocode_llm.py --key YOUR_ANTHROPIC_API_KEY
  python nhrm_geocode_llm.py                               # 讀 .env 中的 ANTHROPIC_API_KEY

輸出：
  data/processed/nhrm_llm_patch.jsonl  每行 {"nhrm_id": N, "location_raw": "...", "lat": ..., "lng": ...}

之後執行 merge_nhrm.py 套用 patch。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import anthropic

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
你是台灣白色恐怖史料的地點判斷專家。
我會給你多位受難者的傳記片段（JSON 陣列，每筆有 id 與 text）。

你的任務：找出每位受難者的**事發地點**，也就是：
- 被捕時所在地（「在○○遭逮捕」「○○工作時被捕」）
- 案件發生地（「任職於○○」「在○○軍中服役」）
- 或最相關的台灣地點（縣、市、鄉、鎮、機構）

**不要**回傳：
- 籍貫/故鄉（「○○省○○縣人」這類出生地）
- 純粹的關押地/監獄名（景美、泰源、綠島——除非整篇都只有這個）
- 中國大陸地名

回傳 JSON 陣列，每筆格式：{"id": N, "location": "地名或null"}
找不到台灣境內事發地點就填 null。只回 JSON，不要說明。"""


def geocode(name: str | None) -> tuple[float, float] | None:
    if not name:
        return None
    sorted_keys = sorted(TAIWAN_LOCATIONS.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in name:
            return TAIWAN_LOCATIONS[key]
    return None


def _parse_response(raw: str) -> list:
    """解析 LLM 回傳的 JSON，容忍常見格式問題。"""
    def _extract_array(text: str) -> str:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]
        return text

    def _cleanup(text: str) -> str:
        text = re.sub(r':\s*None\b', ': null', text)
        text = re.sub(r':\s*(不明|無|空)\s*([,}\]])', r': null\2', text)
        text = re.sub(r',\s*([}\]])', r'\1', text)
        return text

    candidate = _extract_array(raw)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    try:
        return json.loads(_cleanup(candidate))
    except json.JSONDecodeError:
        pass

    # fallback：逐個抽取 {...}
    results = []
    for m in re.finditer(r'\{[^{}]+\}', candidate):
        try:
            results.append(json.loads(m.group()))
        except json.JSONDecodeError:
            try:
                results.append(json.loads(_cleanup(m.group())))
            except json.JSONDecodeError:
                pass
    if results:
        return results

    raise json.JSONDecodeError("無法解析回傳", raw, 0)


def ask_claude_batch(
    client: anthropic.Anthropic,
    items: list[dict],
    retries: int = 6,
) -> dict[int, str | None]:
    """送一批記錄給 Claude，回傳 {nhrm_id: location_name_or_None}。"""
    prompt = json.dumps(items, ensure_ascii=False)

    for attempt in range(retries):
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text.strip()
            parsed = _parse_response(raw)
            result: dict[int, str | None] = {}
            for entry in parsed:
                loc = entry.get("location")
                if loc and loc.lower() != "null" and loc not in ("無", "不明"):
                    result[int(entry["id"])] = loc
                else:
                    result[int(entry["id"])] = None
            return result

        except anthropic.RateLimitError as e:
            retry_after = 60
            try:
                retry_after = int(e.response.headers.get("retry-after", 60))
            except Exception:
                pass
            wait = min(retry_after + 3, 120)
            if attempt < retries - 1:
                print(f"    rate limit，等待 {wait}s 後重試...", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"    批次失敗（rate limit），跳過此批", file=sys.stderr)
                return {int(item["id"]): None for item in items}

        except Exception as e:
            msg = str(e)
            if attempt < retries - 1:
                wait = min(10 * (attempt + 1), 60)
                print(f"    失敗（{msg[:80]}），等待 {wait}s 重試...", file=sys.stderr)
                time.sleep(wait)
            else:
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
        default=os.environ.get("ANTHROPIC_API_KEY", ""),
        help="Anthropic API key（也可設 ANTHROPIC_API_KEY 環境變數或寫進 .env）",
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
    parser.add_argument("--delay", type=float, default=0.5, help="每次 API 請求間隔秒數（預設 0.5）")
    parser.add_argument("--batch-size", type=int, default=10, help="每次 API 呼叫包含幾筆（預設 10）")
    parser.add_argument("--limit", type=int, default=0, help="最多處理幾筆記錄（0=全部）")
    parser.add_argument(
        "--reprocess-sources",
        default="",
        help="重跑指定來源的記錄，逗號分隔，如 native,nhrm_place",
    )
    args = parser.parse_args()

    api_key = args.key.strip()
    if not api_key:
        print("錯誤：請提供 Anthropic API key（--key 參數、ANTHROPIC_API_KEY 環境變數，或 .env 檔案）", file=sys.stderr)
        sys.exit(1)

    reprocess_sources = {s.strip() for s in args.reprocess_sources.split(",") if s.strip()}

    client = anthropic.Anthropic(api_key=api_key)
    patch_path = Path(args.out)

    print("載入 nhrm_merged.json...", file=sys.stderr)
    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    persons = data["persons"]

    candidates = [
        p for p in persons
        if p.get("lat") is None or p.get("location_source") in reprocess_sources
    ]
    print(f"  候選筆數：{len(candidates)}（無座標 + 重跑來源 {reprocess_sources or '無'}）", file=sys.stderr)

    done = load_done(patch_path)
    print(f"  已處理（patch）：{len(done)} 筆", file=sys.stderr)

    pending = [p for p in candidates if p["nhrm_id"] not in done or p.get("location_source") in reprocess_sources]
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

            no_text = [p for p in chunk if not (p.get("introduction") or "").strip()]
            has_text = [p for p in chunk if (p.get("introduction") or "").strip()]

            for p in no_text:
                out_f.write(json.dumps({"nhrm_id": p["nhrm_id"], "location_raw": None, "lat": None, "lng": None}, ensure_ascii=False) + "\n")
                miss += 1

            if has_text:
                items = [
                    {"id": p["nhrm_id"], "text": (p.get("introduction") or "")[:150]}
                    for p in has_text
                ]
                results = ask_claude_batch(client, items)

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
                print(f"  [{processed}/{len(pending)}] hit={hit} miss={miss}", file=sys.stderr)

            if batch_start + bs < len(pending):
                time.sleep(args.delay)

    total_hit = sum(1 for v in done.values() if v.get("lat") is not None) + hit
    print(f"\n完成。本次新增有座標：{hit}，無法定位：{miss}", file=sys.stderr)
    print(f"patch 檔累計有座標：{total_hit} 筆 → {patch_path}", file=sys.stderr)
    print("請再執行 merge_nhrm.py 套用 patch。", file=sys.stderr)


if __name__ == "__main__":
    main()
