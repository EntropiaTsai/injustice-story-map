"""
國家人權記憶庫爬蟲工具。

- search_person：用 Playwright 搜尋（搜尋頁需 JS 渲染）
- get_person_detail：用 httpx 直接 GET HTML（detail 頁 SSR，無需瀏覽器）

可獨立執行：
    python nhrm_scraper.py --name "蕭朝金"
    python nhrm_scraper.py --id 20608
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "https://memory.nhrm.gov.tw"
SEARCH_URL = f"{BASE_URL}/FullSearch/FullSearch"
DETAIL_URL = f"{BASE_URL}/TopicExploration/Person/Detail"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; injustice-story-map-research-bot/1.0; "
        "+https://github.com/EntropiaTsai/injustice-story-map)"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9",
}


async def search_person(name: str) -> list[dict[str, Any]]:
    """以姓名搜尋，回傳候選人清單（含 id、link_text）。搜尋頁需 JS，用 Playwright。"""
    from playwright.async_api import async_playwright

    results: list[dict[str, Any]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(extra_http_headers=_HEADERS)
        await page.goto(f"{SEARCH_URL}?searchKeyword={name}", wait_until="domcontentloaded")

        links = await page.eval_on_selector_all(
            "a[href*='/TopicExploration/Person/Detail/']",
            "els => els.map(el => ({ href: el.href, text: el.innerText.trim() }))",
        )
        await browser.close()

    seen_ids: set[int] = set()
    for link in links:
        m = re.search(r"/Detail/(\d+)", link["href"])
        if not m:
            continue
        pid = int(m.group(1))
        if pid in seen_ids:
            continue
        seen_ids.add(pid)
        results.append({"id": pid, "url": f"{DETAIL_URL}/{pid}", "link_text": link["text"]})

    return results


async def get_person_detail(person_id: int) -> dict[str, Any]:
    """取得特定人員完整資料。detail 頁是 SSR，用 httpx 輕量 GET 即可。"""
    url = f"{DETAIL_URL}/{person_id}"

    async with httpx.AsyncClient(headers=_HEADERS, timeout=20, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text

    # 從 HTML 中擷取 window.fullSearchViewModel = {...}
    m = re.search(r"window\.fullSearchViewModel\s*=\s*(\{.*?\});\s*\n", html, re.DOTALL)
    if not m:
        return {"error": "找不到資料", "person_id": person_id, "url": url}

    try:
        raw = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        return {"error": f"JSON 解析失敗：{e}", "person_id": person_id, "url": url}

    detail = raw.get("DetailViewModel", {})
    main = detail.get("Main") or {}
    recoup_list = detail.get("Recoup") or []

    return {
        "person_id": person_id,
        "url": url,
        "name": main.get("Name"),
        "gender": main.get("Sex"),
        "birth_year": main.get("Birthday_Y"),
        "birth_month": main.get("Birthday_M"),
        "birth_day": main.get("Birthday_D"),
        "death_year": main.get("Death_Y"),
        "province": main.get("Province"),
        "city": main.get("City"),
        "introduction": (main.get("Text") or "").strip() or None,
        "recoup": [r.get("RecoupAll") for r in recoup_list if r.get("RecoupAll")],
    }


# ── 同步包裝（供 agent 使用）──────────────────────────────────────────────────

def search_person_sync(name: str) -> list[dict[str, Any]]:
    return asyncio.run(search_person(name))


def get_person_detail_sync(person_id: int) -> dict[str, Any]:
    return asyncio.run(get_person_detail(person_id))


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="國家人權記憶庫爬蟲")
    parser.add_argument("--name", help="以姓名搜尋")
    parser.add_argument("--id", type=int, dest="person_id", help="以人員 ID 查詢詳細資料")
    args = parser.parse_args()

    if args.name:
        results = asyncio.run(search_person(args.name))
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif args.person_id:
        detail = asyncio.run(get_person_detail(args.person_id))
        print(json.dumps(detail, ensure_ascii=False, indent=2))
    else:
        parser.print_help()
        sys.exit(1)
