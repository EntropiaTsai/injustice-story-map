"""
nhrm_audit.py — 批次審查 NHRM 圖卡資料

對每筆有簡介的 NHRM 記錄：
  1. Python 層：偵測排版問題（行政樣板文、重複段落、過短）
  2. Gemini 層：產生事實摘要 + 抽出案發地／被捕地
  3. 輸出 JSONL（可斷點續跑）

用法：
  cd scripts/tools
  python nhrm_audit.py                  # 全量跑（可中斷續跑）
  python nhrm_audit.py --limit 100      # 測試前 100 筆
  python nhrm_audit.py --batch-size 3   # 每次送 3 筆給 Gemini
  python nhrm_audit.py --no-llm         # 只跑 Python 格式檢查
  python nhrm_audit.py --apply-patches  # 把結果轉成 nhrm_llm_patch.jsonl 條目

輸出：
  data/processed/nhrm_audit.jsonl       每行一筆審查結果
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MERGED = REPO / "data" / "processed" / "nhrm_merged.json"
AUDIT_OUT = REPO / "data" / "processed" / "nhrm_audit.jsonl"
PATCH_OUT = REPO / "data" / "processed" / "nhrm_llm_patch.jsonl"

# 只從 merge_nhrm.py 的 TAIWAN_LOCATIONS 中取城市/地區名（不含機構名）
# 讓 LLM 抽出地名後做 geocoding 用
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
    "綠島": (22.6607, 121.4920), "火燒島": (22.6607, 121.4920),
    "泰源": (23.1167, 121.2500),
    "馬場町": (25.0302, 121.5057),
    "六張犁": (25.0244, 121.5607),
    "內湖": (25.0630, 121.5939),
    "景美": (24.9984, 121.5415),
    "新店": (24.9716, 121.5378),
    "板橋": (25.0141, 121.4617),
    "淡水": (25.1711, 121.4497),
    "三重": (25.0620, 121.4924),
    "中和": (24.9999, 121.4889),
    "永和": (25.0133, 121.5195),
    "台北": (25.0330, 121.5654), "臺北": (25.0330, 121.5654),
    "北市": (25.0330, 121.5654),
    "基隆": (25.1276, 121.7392),
    "桃園": (24.9937, 121.3010),
    "新竹": (24.8066, 120.9686),
    "苗栗": (24.5602, 120.8214),
    "竹南": (24.6874, 120.8639),
    "中壢": (24.9636, 121.2249),
    "台中": (24.1477, 120.6736), "臺中": (24.1477, 120.6736),
    "豐原": (24.2537, 120.7196),
    "清水": (24.3636, 120.5638),
    "土城": (24.9750, 121.4378),
    "彰化": (24.0684, 120.5820),
    "員林": (23.9586, 120.5710),
    "南投": (23.9609, 120.9718),
    "埔里": (23.9611, 120.9735),
    "霧峰": (24.0573, 120.7178),
    "雲林": (23.7092, 120.4313),
    "斗六": (23.7104, 120.5428),
    "虎尾": (23.7082, 120.4394),
    "嘉義": (23.4801, 120.4491),
    "台南": (22.9999, 120.2270), "臺南": (22.9999, 120.2270),
    "新營": (23.3116, 120.3123),
    "善化": (23.1434, 120.2977),
    "歸仁": (22.9654, 120.2914),
    "高雄": (22.6273, 120.3014),
    "岡山": (22.7953, 120.2949),
    "鳳山": (22.6271, 120.3567),
    "旗山": (22.8878, 120.4806),
    "左營": (22.6911, 120.2954),
    "屏東": (22.5519, 120.5487),
    "澎湖": (23.5711, 119.5795),
    "馬公": (23.5642, 119.5631),
    "花蓮": (23.9872, 121.6015),
    "玉里": (23.6327, 121.3149),
    "台東": (22.7972, 121.0713), "臺東": (22.7972, 121.0713),
    "宜蘭": (24.7021, 121.7378),
    "羅東": (24.6776, 121.7712),
    "士林": (25.0878, 121.5240),
    "北投": (25.1317, 121.4989),
    "木柵": (24.9983, 121.5681),
    "萬華": (25.0374, 121.5000),
    "大稻埕": (25.0568, 121.5108),
    "汐止": (25.0698, 121.6604),
    "金瓜石": (25.1093, 121.8525),
    "蘇澳": (24.5978, 121.8438),
    "頭城": (24.8460, 121.8188),
    "關山": (23.0528, 121.1672),
    "池上": (23.1089, 121.2233),
    "成功": (23.0994, 121.3706),
    "金門": (24.4493, 118.3765),
    "馬祖": (26.1504, 119.9318),
}

ADMIN_PATTERN = re.compile(r"本案為.{0,30}申請補償")

GEMINI_SYSTEM = """\
你是台灣白色恐怖史料的分析專家。我會給你多位受難者的基本資料與簡介文字（JSON 陣列）。

對每筆記錄，請完成兩件事：
1. **summary**：2-3 句事實摘要，描述此人的身份、案由、判決與釋放時間。僅陳述事實，不渲染情感，不使用「飽受」「悲慘」等詞語。用繁體中文。
2. **arrest_location**：從簡介中找出**最精確的**「被捕地點」或「案發地點」。
   - 優先抓：**完整地址**（路名＋號碼，如「台北市中山北路二段55號」）
   - 其次：機構全名（「臺灣省保安司令部」「○○工廠」）＋所在縣市
   - 再次：鄉鎮區名（「○○縣○○鄉」「○○市○○區」），需含縣市
   - 注意：民國年代地名用舊制（如台南縣安定鄉），**原文怎麼寫就怎麼填**，不要自行更新地名
   - **不要**填入：籍貫/出生地、監獄/關押地（景美、綠島、泰源、新生總隊等，除非整篇都只有這個）、中國大陸地名
   - 找不到明確的案發/被捕地點就填 null

回傳 JSON 陣列，格式：[{"id": N, "summary": "...", "arrest_location": "地址或null"}, ...]
只回 JSON，不要說明文字。"""


def geocode_dict(text: str | None) -> tuple[float, float] | None:
    """查字典，最長鍵優先。"""
    if not text:
        return None
    sorted_keys = sorted(TAIWAN_LOCATIONS.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in text:
            return TAIWAN_LOCATIONS[key]
    return None


# 2010/2014 縣市合併：舊縣名 → 新市名
_COUNTY_MERGE: dict[str, str] = {
    "台北縣": "新北市", "臺北縣": "新北市",
    "台中縣": "台中市", "臺中縣": "臺中市",
    "台南縣": "台南市", "臺南縣": "臺南市",
    "高雄縣": "高雄市",
    "桃園縣": "桃園市",
}

def normalize_legacy_address(text: str) -> str:
    """把白色恐怖年代的舊地名轉成現行地名，供 Nominatim 使用。"""
    result = text
    for old, new in _COUNTY_MERGE.items():
        if old in result:
            result = result.replace(old, new)
            # 直轄市合併後，鄉/鎮 升格為 區
            result = re.sub(r"([^\s]{2,4})[鄉鎮](?=[^市縣]|$)", r"\1區", result)
            break
    # 台 ↔ 臺 不影響 Nominatim，保留原字即可
    return result


def geocode_nominatim(address: str, retries: int = 2) -> tuple[float, float] | None:
    """用 OpenStreetMap Nominatim 查精確地址（限台灣）。有 rate limit，1 req/s。"""
    import urllib.parse, urllib.request as ur

    def _query(q: str) -> tuple[float, float] | None:
        params = urllib.parse.urlencode({
            "q": q, "format": "jsonv2",
            "countrycodes": "tw", "limit": 1, "accept-language": "zh-TW",
        })
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        req = ur.Request(url, headers={"User-Agent": "nhrm-audit/1.0 (injustice-story-map)"})
        with ur.urlopen(req, timeout=10) as resp:
            results = json.loads(resp.read().decode())
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
        return None

    for attempt in range(retries):
        try:
            coords = _query(address)
            if coords:
                return coords
            # 舊地名轉換後再查一次
            normalized = normalize_legacy_address(address)
            if normalized != address:
                time.sleep(1.1)
                coords = _query(normalized)
                if coords:
                    return coords
        except Exception:
            if attempt < retries - 1:
                time.sleep(1.5)
    return None


def geocode(text: str | None, use_nominatim: bool = False) -> tuple[float, float] | None:
    """字典優先；若 use_nominatim 且字典查不到則嘗試 Nominatim。"""
    coords = geocode_dict(text)
    if coords:
        return coords
    if use_nominatim and text and len(text) > 4:
        time.sleep(1.1)  # Nominatim rate limit: 1 req/s
        return geocode_nominatim(text)
    return None


def check_format_issues(intro: str) -> list[str]:
    issues = []
    if ADMIN_PATTERN.search(intro) and len(intro) < 200:
        issues.append("admin_only")
    if len(intro) < 30:
        issues.append("too_short")
    paras = [p.strip() for p in intro.split("\n\n") if p.strip()]
    seen: set[str] = set()
    for para in paras:
        if para in seen:
            issues.append("duplicate_paragraph")
            break
        seen.add(para)
    # Check duplicate sentences within paragraph
    sentences = re.split(r"[。！？\n]", intro)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    seen_s: set[str] = set()
    for s in sentences:
        if s in seen_s:
            issues.append("duplicate_sentence")
            break
        seen_s.add(s)
    return issues


def load_done(path: Path) -> set[int]:
    done: set[int] = set()
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        obj = json.loads(line)
                        done.add(obj["nhrm_id"])
                    except (json.JSONDecodeError, KeyError):
                        pass
    return done


def load_env() -> None:
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


def _parse_llm_json(raw: str) -> list[dict]:
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"回傳不含 JSON 陣列: {raw[:200]}")
    return json.loads(raw[start : end + 1])


def call_openai_compat(records: list[dict], retries: int = 4) -> list[dict]:
    """呼叫 OpenAI 相容 API（LiteLLM proxy 等），回傳 [{id, summary, arrest_location}, ...]。

    環境變數：
      OPENAI_API_BASE  - API 基礎 URL，如 https://api.twinkleai.tw/v1
      OPENAI_API_KEY   - API 金鑰（以 sk- 開頭）
      OPENAI_MODEL     - 模型名稱（預設 gpt-4o-mini）
    """
    import urllib.request

    base_url = os.environ.get("OPENAI_API_BASE", "").rstrip("/")
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()

    if not base_url:
        raise RuntimeError("缺少 OPENAI_API_BASE 環境變數")
    if not api_key:
        raise RuntimeError("缺少 OPENAI_API_KEY 環境變數")

    prompt = json.dumps(records, ensure_ascii=False)
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": GEMINI_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 2048,
    }).encode("utf-8")

    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                f"{base_url}/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            raw = data["choices"][0]["message"]["content"].strip()
            return _parse_llm_json(raw)
        except Exception as e:
            msg = str(e)
            if attempt < retries - 1:
                wait = min(10 * (attempt + 1), 60)
                print(f"    OpenAI API 失敗（{msg[:80]}），等待 {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"    OpenAI API 批次失敗，跳過：{msg[:120]}", file=sys.stderr)
                return []
    return []


def call_claude(records: list[dict], retries: int = 4) -> list[dict]:
    """呼叫 Claude Haiku，回傳 [{id, summary, arrest_location}, ...]。"""
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("缺少 ANTHROPIC_API_KEY")

    client = anthropic.Anthropic(api_key=api_key)
    prompt = json.dumps(records, ensure_ascii=False)

    for attempt in range(retries):
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
                system=GEMINI_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text.strip()
            return _parse_llm_json(raw)
        except Exception as e:
            msg = str(e)
            if "rate" in msg.lower() or "429" in msg:
                wait = min(30 * (attempt + 1), 120)
            else:
                wait = min(10 * (attempt + 1), 60)
            if attempt < retries - 1:
                print(f"    Claude 失敗（{msg[:80]}），等待 {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"    Claude 批次失敗，跳過：{msg[:120]}", file=sys.stderr)
                return []
    return []


def call_gemini(records: list[dict], retries: int = 4) -> list[dict]:
    """呼叫 Gemini，回傳 [{id, summary, arrest_location}, ...]。"""
    import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("缺少 GEMINI_API_KEY")

    genai.configure(api_key=api_key)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip()
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=GEMINI_SYSTEM,
    )

    prompt = json.dumps(records, ensure_ascii=False)

    for attempt in range(retries):
        try:
            resp = model.generate_content(prompt)
            raw = (resp.text or "").strip()
            return _parse_llm_json(raw)
        except Exception as e:
            if attempt < retries - 1:
                wait = min(15 * (attempt + 1), 60)
                print(f"    Gemini 失敗（{str(e)[:80]}），等待 {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"    Gemini 批次失敗，跳過：{str(e)[:120]}", file=sys.stderr)
                return []
    return []


def process_batch(records: list[dict], no_llm: bool, llm_backend: str = "claude", use_nominatim: bool = False) -> list[dict]:
    """處理一批記錄，回傳審查結果。"""
    results = []

    if no_llm:
        for rec in records:
            intro = rec.get("introduction", "") or ""
            results.append({
                "nhrm_id": rec["nhrm_id"],
                "name": rec["name"],
                "summary": None,
                "arrest_location": None,
                "arrest_lat": None,
                "arrest_lng": None,
                "format_issues": check_format_issues(intro),
                "current_location_source": rec.get("location_source"),
                "current_location_raw": rec.get("location_raw"),
            })
        return results

    # Prepare LLM input (truncate intro to 400 chars to save tokens)
    llm_input = [
        {
            "id": rec["nhrm_id"],
            "name": rec["name"],
            "intro": (rec.get("introduction") or "")[:400],
        }
        for rec in records
    ]

    if llm_backend == "gemini":
        llm_out = call_gemini(llm_input)
    elif llm_backend == "openai":
        llm_out = call_openai_compat(llm_input)
    else:
        llm_out = call_claude(llm_input)
    gemini_map = {int(g["id"]): g for g in llm_out if "id" in g}

    for rec in records:
        intro = rec.get("introduction", "") or ""
        nid = rec["nhrm_id"]
        gdata = gemini_map.get(nid, {})

        arrest_loc = gdata.get("arrest_location") or None
        if arrest_loc and arrest_loc.lower() in ("null", "无", "無", "不明", "none"):
            arrest_loc = None

        coords = geocode(arrest_loc, use_nominatim=use_nominatim)

        results.append({
            "nhrm_id": nid,
            "name": rec["name"],
            "summary": gdata.get("summary") or None,
            "arrest_location": arrest_loc,
            "arrest_lat": coords[0] if coords else None,
            "arrest_lng": coords[1] if coords else None,
            "format_issues": check_format_issues(intro),
            "current_location_source": rec.get("location_source"),
            "current_location_raw": rec.get("location_raw"),
        })

    return results


def apply_patches(audit_path: Path, patch_path: Path) -> None:
    """
    從 audit JSONL 生成 nhrm_llm_patch 條目：
    - 只處理有 arrest_location 且能 geocode 的記錄
    - 只覆蓋 location_source 不是 twtjdb 的記錄
    - 如果 arrest_location 與 current_location_raw 相同則跳過
    """
    # 讀取現有 patch
    existing_patches: dict[int, dict] = {}
    if patch_path.exists():
        with open(patch_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        obj = json.loads(line)
                        existing_patches[obj["nhrm_id"]] = obj
                    except (json.JSONDecodeError, KeyError):
                        pass

    new_patches: list[dict] = []
    skipped = 0
    already = 0

    with open(audit_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            nid = rec.get("nhrm_id")
            if not nid:
                continue

            arrest_loc = rec.get("arrest_location")
            arrest_lat = rec.get("arrest_lat")
            arrest_lng = rec.get("arrest_lng")

            if not arrest_loc or arrest_lat is None or arrest_lng is None:
                skipped += 1
                continue

            cur_src = rec.get("current_location_source")
            if cur_src == "twtjdb":
                skipped += 1
                continue

            cur_raw = rec.get("current_location_raw") or ""
            if arrest_loc in cur_raw:
                already += 1
                continue

            # 已有 force patch 就跳過
            if nid in existing_patches and existing_patches[nid].get("force"):
                already += 1
                continue

            new_patches.append({
                "nhrm_id": nid,
                "location_raw": arrest_loc,
                "lat": arrest_lat,
                "lng": arrest_lng,
                "source": "audit",
            })

    print(f"  新增 patch 條目：{len(new_patches)}", file=sys.stderr)
    print(f"  已有座標/相同地點：{already}", file=sys.stderr)
    print(f"  無法 geocode：{skipped}", file=sys.stderr)

    if not new_patches:
        print("  無新 patch，結束。", file=sys.stderr)
        return

    with open(patch_path, "a", encoding="utf-8") as f:
        for p in new_patches:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"  已附加至 {patch_path}", file=sys.stderr)


def main() -> None:
    load_env()

    parser = argparse.ArgumentParser(description="NHRM 圖卡批次審查")
    parser.add_argument("--input", default=str(MERGED), help="nhrm_merged.json 路徑")
    parser.add_argument("--out", default=str(AUDIT_OUT), help="輸出 audit JSONL")
    parser.add_argument("--patch-out", default=str(PATCH_OUT), help="nhrm_llm_patch.jsonl 路徑")
    parser.add_argument("--batch-size", type=int, default=5, help="每次送幾筆給 LLM（預設 5）")
    parser.add_argument("--limit", type=int, default=0, help="最多處理幾筆（0=全部）")
    parser.add_argument("--delay", type=float, default=0.5, help="批次間延遲秒數（預設 0.5）")
    parser.add_argument("--no-llm", action="store_true", help="只跑 Python 格式檢查，不呼叫 LLM")
    parser.add_argument("--llm", default="claude", choices=["claude", "gemini", "openai"], help="使用的 LLM 後端（預設 claude；openai=OpenAI 相容 API）")
    parser.add_argument("--nominatim", action="store_true", help="字典查不到時用 Nominatim 精確 geocoding（限 1 req/s）")
    parser.add_argument("--apply-patches", action="store_true", help="將 audit 結果轉為 llm_patch 條目後結束")
    args = parser.parse_args()

    audit_path = Path(args.out)
    patch_path = Path(args.patch_out)

    if args.apply_patches:
        print("套用 audit 結果為 geocoding patch...", file=sys.stderr)
        apply_patches(audit_path, patch_path)
        return

    print("載入 nhrm_merged.json...", file=sys.stderr)
    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    persons = data["persons"]

    # 篩選有實質簡介的記錄
    candidates = [
        p for p in persons
        if (p.get("introduction") or "").strip()
        and len((p.get("introduction") or "").strip()) >= 30
        and not (ADMIN_PATTERN.search(p.get("introduction") or "") and len(p.get("introduction") or "") < 200)
    ]
    print(f"  有效簡介記錄：{len(candidates)}", file=sys.stderr)

    done = load_done(audit_path)
    print(f"  已審查：{len(done)} 筆", file=sys.stderr)

    pending = [p for p in candidates if p["nhrm_id"] not in done]
    if args.limit > 0:
        pending = pending[: args.limit]
    print(f"  待處理：{len(pending)} 筆（批次大小 {args.batch_size}）", file=sys.stderr)

    if not pending:
        print("  全部已處理。", file=sys.stderr)
        return

    bs = args.batch_size
    processed = 0
    errors = 0

    with open(audit_path, "a", encoding="utf-8") as out_f:
        for batch_start in range(0, len(pending), bs):
            chunk = pending[batch_start : batch_start + bs]
            try:
                results = process_batch(chunk, no_llm=args.no_llm, llm_backend=args.llm, use_nominatim=args.nominatim)
                for res in results:
                    out_f.write(json.dumps(res, ensure_ascii=False) + "\n")
                out_f.flush()
                processed += len(results)
            except Exception as e:
                errors += 1
                print(f"  批次 {batch_start} 失敗：{e}", file=sys.stderr)

            if processed % (bs * 20) == 0 or processed >= len(pending):
                pct = processed / len(pending) * 100
                print(f"  [{processed}/{len(pending)}] {pct:.1f}% 錯誤批次:{errors}", file=sys.stderr)

            if batch_start + bs < len(pending) and not args.no_llm:
                time.sleep(args.delay)

    print(f"\n完成。已審查 {processed} 筆，錯誤批次 {errors} 個。", file=sys.stderr)
    print(f"輸出：{audit_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
