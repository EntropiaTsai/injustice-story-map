"""
從國家人權記憶庫人物清單頁爬取全部記錄。

流程：
1. 用 Playwright 訪問 6 個年代清單頁，收集所有 person ID
2. 用 httpx 逐一抓 detail 頁（SSR，不需瀏覽器）
3. 解析所有欄位，包含傳記、刑罰、平復補償、twtjdb 跨資料庫連結
4. 輸出 JSONL（每行一筆，支援斷點續跑）

用法：
    python nhrm_full_scraper.py --out data/nhrm_all.jsonl
    python nhrm_full_scraper.py --out data/nhrm_all.jsonl   # 中斷後重跑，自動跳過已處理
    python nhrm_full_scraper.py --collect-ids               # 只收集 ID 清單，印到 stdout
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "https://memory.nhrm.gov.tw"
LIST_URL = f"{BASE_URL}/TopicExploration/Person"
DETAIL_URL = f"{BASE_URL}/TopicExploration/Person/Detail"
DECADES = ["1940", "1950", "1960", "1970", "1980", "1990"]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; injustice-story-map-research-bot/1.0; "
        "+https://github.com/EntropiaTsai/injustice-story-map)"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9",
}


# ── 收集所有人物 ID ────────────────────────────────────────────────────────────

async def collect_all_ids() -> list[dict[str, str]]:
    """
    訪問 6 個年代清單頁，回傳 list of {nhrm_id, name, decade}。
    清單頁需 JS 渲染，用 Playwright。
    """
    from playwright.async_api import async_playwright

    records: list[dict[str, str]] = []
    seen: set[str] = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(extra_http_headers=_HEADERS)

        for decade in DECADES:
            print(f"  [collect] 年代 {decade}...", file=sys.stderr)
            await page.goto(f"{LIST_URL}?Year={decade}", wait_until="networkidle", timeout=30000)

            links = await page.eval_on_selector_all(
                "a[href*='/TopicExploration/Person/Detail/']",
                "els => els.map(el => ({ href: el.href, text: el.innerText.trim() }))",
            )

            for lnk in links:
                m = re.search(r"/Detail/(\d+)", lnk["href"])
                if not m:
                    continue
                nid = m.group(1)
                if nid in seen:
                    continue
                seen.add(nid)
                # 去掉括號內別名
                name = re.sub(r"[\(（].*?[\)）]", "", lnk["text"]).strip()
                name = re.sub(r"\s+", "", name)
                records.append({"nhrm_id": nid, "name": name, "decade": decade})

            print(f"    → 本年代 {len(links)} 筆，累計 {len(seen)} 筆", file=sys.stderr)

        await browser.close()

    return records


# ── 抓單筆 detail ──────────────────────────────────────────────────────────────

def _extract_twtjdb_ids(penalty_list: list[dict]) -> list[str]:
    ids: list[str] = []
    for p in penalty_list:
        url = p.get("URL") or ""
        m = re.search(r"content-(\d+)-\d+", url)
        if m:
            ids.append(m.group(1))
    return list(dict.fromkeys(ids))  # 去重保序


def _parse_detail_html(html: str, nhrm_id: int) -> dict[str, Any]:
    url = f"{DETAIL_URL}/{nhrm_id}"

    m = re.search(r"window\.fullSearchViewModel\s*=\s*(\{.*?\});\s*\n", html, re.DOTALL)
    if not m:
        return {"error": "找不到 viewModel", "nhrm_id": nhrm_id, "url": url}

    try:
        raw = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        return {"error": f"JSON 解析失敗：{e}", "nhrm_id": nhrm_id, "url": url}

    detail = raw.get("DetailViewModel", {})
    main = detail.get("Main") or {}
    penalty_list = detail.get("Penalty") or []
    recoup_list = detail.get("Recoup") or []
    tag_list = detail.get("TagResult") or []

    # 刑罰記錄（含 twtjdb_id）
    penalty_records = []
    for p in penalty_list:
        url_ref = p.get("URL") or ""
        tid_m = re.search(r"content-(\d+)-\d+", url_ref)
        penalty_records.append({
            "judg_year_roc": p.get("Judg_Year"),
            "judg_no": p.get("Judg_NO"),
            "occupation": p.get("Occupation"),
            "age": p.get("Age"),
            "judgment": p.get("Judgment"),
            "term": p.get("Term"),
            "penalty_text": p.get("Penalty"),
            "twtjdb_id": tid_m.group(1) if tid_m else None,
            "twtjdb_url": url_ref or None,
        })

    # 傳記文字：去掉 HTML 標籤，保留換行語意
    intro_html = main.get("Text") or ""
    intro_text = re.sub(r"<br\s*/?>", "\n", intro_html, flags=re.IGNORECASE)
    intro_text = re.sub(r"<[^>]+>", "", intro_text).strip() or None

    return {
        "nhrm_id": nhrm_id,
        "url": f"{DETAIL_URL}/{nhrm_id}",
        "name": main.get("Name"),
        "nickname": main.get("NickName") or None,
        "gender": main.get("Sex"),
        "birth_year": main.get("Birthday_Y"),
        "birth_month": main.get("Birthday_M"),
        "birth_day": main.get("Birthday_D"),
        "death_year": main.get("Death_Y"),
        "province": main.get("Province"),
        "city": main.get("City"),
        "place": main.get("Place") or None,          # 相關地點（關押地等）
        "url_green_island": main.get("URL_GreenIsland") or None,
        "url_jingmei": main.get("URL_Jingmei") or None,
        "introduction": intro_text,
        "penalty": penalty_records,
        "twtjdb_ids": _extract_twtjdb_ids(penalty_list),
        "recoup": [r.get("RecoupAll") for r in recoup_list if r.get("RecoupAll")],
        "cases": [                                     # 所屬案件
            {"id": t["K_Id"], "name": t["CName"]}
            for t in tag_list if t.get("Type") == "Event"
        ],
        "related_persons": [                           # 同案相關人物
            {"nhrm_id": t["K_Id"], "name": t["CName"]}
            for t in tag_list if t.get("Type") == "Person"
        ],
    }


async def fetch_detail(nhrm_id: int, client: httpx.AsyncClient) -> dict[str, Any]:
    resp = await client.get(f"{DETAIL_URL}/{nhrm_id}")
    resp.raise_for_status()
    return _parse_detail_html(resp.text, nhrm_id)


# ── 斷點續跑 ──────────────────────────────────────────────────────────────────

def _load_done_ids(out_path: Path) -> set[str]:
    done: set[str] = set()
    if not out_path.exists():
        return done
    with open(out_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                if "nhrm_id" in row:
                    done.add(str(row["nhrm_id"]))
            except json.JSONDecodeError:
                pass
    return done


# ── 主流程 ────────────────────────────────────────────────────────────────────

async def run(out_path: Path, delay: float) -> None:
    # Step 1：收集所有 ID
    print("[step 1] 從清單頁收集人物 ID...", file=sys.stderr)
    records = await collect_all_ids()
    print(f"  共 {len(records)} 筆", file=sys.stderr)

    # Step 2：斷點續跑
    done_ids = _load_done_ids(out_path)
    if done_ids:
        print(f"[resume] 已跳過 {len(done_ids)} 筆", file=sys.stderr)

    total = len(records)
    out_file = open(out_path, "a", encoding="utf-8")

    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=20, follow_redirects=True) as client:
            for i, rec in enumerate(records):
                nid = rec["nhrm_id"]
                if nid in done_ids:
                    continue

                print(f"[{i+1}/{total}] {rec['name']} (ID {nid})", file=sys.stderr)

                try:
                    result = await fetch_detail(int(nid), client)
                    result["decade"] = rec["decade"]
                except Exception as e:
                    print(f"  [error] {e}", file=sys.stderr)
                    result = {"nhrm_id": int(nid), "name": rec["name"], "decade": rec["decade"], "error": str(e)}

                line = json.dumps(result, ensure_ascii=False)
                out_file.write(line + "\n")
                out_file.flush()

                if i < total - 1:
                    await asyncio.sleep(delay)
    finally:
        out_file.close()

    print(f"\n完成。輸出：{out_path}", file=sys.stderr)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NHRM 人物全量爬蟲")
    parser.add_argument("--out", required=False, help="輸出 JSONL 路徑（預設：nhrm_all.jsonl）")
    parser.add_argument("--collect-ids", action="store_true", help="只收集 ID 清單，印到 stdout")
    parser.add_argument("--delay", type=float, default=1.0, help="每筆之間的延遲秒數（預設 1）")
    args = parser.parse_args()

    if args.collect_ids:
        records = asyncio.run(collect_all_ids())
        for r in records:
            print(json.dumps(r, ensure_ascii=False))
        sys.exit(0)

    out = Path(args.out) if args.out else Path("nhrm_all.jsonl")
    asyncio.run(run(out, args.delay))
