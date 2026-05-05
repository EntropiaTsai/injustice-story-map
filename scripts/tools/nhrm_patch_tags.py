"""
補丁：為舊版爬蟲輸出補上 cases、related_persons、image_url、documents 欄位。

用法：
    python nhrm_patch_tags.py --input data/raw/nhrm_all.jsonl
    （原地覆寫，先備份再跑）
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

import httpx

DETAIL_URL = "https://memory.nhrm.gov.tw/TopicExploration/Person/Detail"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; injustice-story-map-research-bot/1.0; "
        "+https://github.com/EntropiaTsai/injustice-story-map)"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9",
}


def _extract_missing(html: str) -> dict:
    m = re.search(r"window\.fullSearchViewModel\s*=\s*(\{.*?\});\s*\n", html, re.DOTALL)
    if not m:
        return {"cases": [], "related_persons": [], "image_url": None, "documents": []}
    try:
        raw = json.loads(m.group(1))
    except json.JSONDecodeError:
        return {"cases": [], "related_persons": [], "image_url": None, "documents": []}

    detail = raw.get("DetailViewModel", {})
    main = detail.get("Main") or {}
    tag_list = detail.get("TagResult") or []

    return {
        "cases": [
            {"id": t["K_Id"], "name": t["CName"]}
            for t in tag_list if t.get("Type") == "Event"
        ],
        "related_persons": [
            {"nhrm_id": t["K_Id"], "name": t["CName"]}
            for t in tag_list if t.get("Type") == "Person"
        ],
        "image_url": main.get("ImagePath") or None,
        "documents": [
            {
                "doc_id": d.get("H_Main_Id"),
                "title": d.get("Judg_Name"),
                "authority": d.get("Authority") or None,
                "related_persons": d.get("Related_Person") or None,
                "date": d.get("Auth_Date") or None,
                "image_url": d.get("OrlPath") or None,
            }
            for d in (detail.get("HistoricalSpaceList") or [])
        ],
    }


async def patch(input_path: Path, delay: float) -> None:
    lines = input_path.read_text(encoding="utf-8").splitlines()
    records = []
    for line in lines:
        line = line.strip()
        if line:
            records.append(json.loads(line))

    MISSING_FIELDS = {"cases", "related_persons", "image_url", "documents"}
    need_patch = [r for r in records if not r.get("error") and not MISSING_FIELDS.issubset(r.keys())]
    print(f"共 {len(records)} 筆，需補 {len(need_patch)} 筆", file=sys.stderr)

    if not need_patch:
        print("全部欄位已完整，無需補丁。", file=sys.stderr)
        return

    patched_map: dict[int, dict] = {}

    async with httpx.AsyncClient(headers=_HEADERS, timeout=20, follow_redirects=True) as client:
        for i, rec in enumerate(need_patch):
            nid = rec["nhrm_id"]
            print(f"[{i+1}/{len(need_patch)}] {rec.get('name', '?')} (ID {nid})", file=sys.stderr)
            try:
                resp = await client.get(f"{DETAIL_URL}/{nid}")
                resp.raise_for_status()
                patched_map[nid] = _extract_missing(resp.text)
            except Exception as e:
                print(f"  [error] {e}", file=sys.stderr)
                patched_map[nid] = {"cases": [], "related_persons": [], "image_url": None, "documents": []}

            if i < len(need_patch) - 1:
                await asyncio.sleep(delay)

    # 寫回
    out_lines = []
    for rec in records:
        nid = rec.get("nhrm_id")
        if nid in patched_map:
            rec.update(patched_map[nid])
        else:
            for f in MISSING_FIELDS:
                rec.setdefault(f, [] if f != "image_url" else None)
        out_lines.append(json.dumps(rec, ensure_ascii=False))

    input_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"完成，已覆寫 {input_path}", file=sys.stderr)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="要補丁的 JSONL 檔路徑")
    parser.add_argument("--delay", type=float, default=0.5, help="每筆延遲秒數（預設 0.5）")
    args = parser.parse_args()

    asyncio.run(patch(Path(args.input), args.delay))
