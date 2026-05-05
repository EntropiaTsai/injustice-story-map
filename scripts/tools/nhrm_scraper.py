"""
國家人權記憶庫 Playwright 爬蟲工具。

可獨立執行：
    python nhrm_scraper.py --name "蕭朝金"
    python nhrm_scraper.py --id 20608

也可作為模組被 agent 匯入：
    from tools.nhrm_scraper import search_person, get_person_detail
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Any

BASE_URL = "https://memory.nhrm.gov.tw"
SEARCH_URL = f"{BASE_URL}/FullSearch/FullSearch"
DETAIL_URL = f"{BASE_URL}/TopicExploration/Person/Detail"


async def search_person(name: str) -> list[dict[str, Any]]:
    """以姓名搜尋，回傳候選人清單（含 id、姓名、出生年、簡介摘要）。"""
    from playwright.async_api import async_playwright

    results: list[dict[str, Any]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f"{SEARCH_URL}?searchKeyword={name}", wait_until="domcontentloaded")

        # 找所有指向 Person/Detail 的連結
        links = await page.eval_on_selector_all(
            "a[href*='/TopicExploration/Person/Detail/']",
            "els => els.map(el => ({ href: el.href, text: el.innerText.trim() }))",
        )

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

        await browser.close()

    return results


async def get_person_detail(person_id: int) -> dict[str, Any]:
    """取得特定人員的完整資料（姓名、出生年、籍貫、簡介、平復補償）。"""
    from playwright.async_api import async_playwright

    url = f"{DETAIL_URL}/{person_id}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")

        # 直接從頁面內嵌的 JS 物件取資料，不需解析 HTML
        raw: dict | None = await page.evaluate(
            "() => window.fullSearchViewModel ?? null"
        )
        await browser.close()

    if not raw:
        return {"error": "找不到資料", "person_id": person_id, "url": url}

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


# ── 同步包裝（供 agent function calling 使用）─────────────────────────────────

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
