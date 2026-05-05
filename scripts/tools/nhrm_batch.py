"""
純 Playwright 批次查詢國家人權記憶庫，不需要 LLM API。

比對邏輯：
  1. 搜尋姓名，找到完全一致的候選
  2. 若只有一筆完全一致 → 取詳細資料
  3. 若有多筆 → 全部取回，標記 ambiguous=true
  4. 若無完全一致 → found=false

用法：
    # 從 make_name_list.py 產生的 JSONL 批次查詢
    python nhrm_batch.py --jsonl names.jsonl --out results.jsonl

    # 支援斷點續跑（已處理的 twtjdb_id 自動跳過）
    python nhrm_batch.py --jsonl names.jsonl --out results.jsonl
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nhrm_scraper import search_person, get_person_detail


async def lookup_one(name: str) -> list[dict[str, Any]]:
    """搜尋並取回完全符合姓名的詳細資料。"""
    candidates = await search_person(name)

    # link_text 格式：「人物\n{序號}\n{姓名}\n{摘要}」，取 index 2
    def extract_name(link_text: str) -> str:
        parts = link_text.split("\n")
        if len(parts) >= 3 and parts[0].strip() == "人物":
            return parts[2].strip()
        # fallback：取第一個非數字、非「人物」的部分
        for p in parts:
            p = p.strip()
            if p and not p.isdigit() and p != "人物":
                return p
        return link_text.strip()

    matched = [c for c in candidates if extract_name(c["link_text"]) == name]

    if not matched:
        return [{"found": False, "name": name}]

    results = []
    for c in matched:
        detail = await get_person_detail(c["id"])
        detail["found"] = True
        detail["ambiguous"] = len(matched) > 1
        results.append(detail)
    return results


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
                if "twtjdb_id" in row:
                    done.add(str(row["twtjdb_id"]))
            except json.JSONDecodeError:
                pass
    return done


async def run_batch(rows: list[dict[str, Any]], out_path: Path | None, delay: float) -> None:
    done_ids = _load_done_ids(out_path) if out_path else set()
    if done_ids:
        print(f"[resume] 已跳過 {len(done_ids)} 筆", file=sys.stderr)

    out_file = open(out_path, "a", encoding="utf-8") if out_path else None

    try:
        for i, row in enumerate(rows):
            tid = str(row.get("twtjdb_id", "")) or None
            if tid and tid in done_ids:
                continue

            name = row["name"]
            print(f"[{i+1}/{len(rows)}] {name}", file=sys.stderr)

            try:
                results = await lookup_one(name)
            except Exception as e:
                print(f"  [error] {e}", file=sys.stderr)
                results = [{"found": False, "name": name, "error": str(e)}]

            for result in results:
                if tid:
                    result["twtjdb_id"] = tid
                line = json.dumps(result, ensure_ascii=False)
                print(line)
                sys.stdout.flush()
                if out_file:
                    out_file.write(line + "\n")
                    out_file.flush()

            if i < len(rows) - 1:
                await asyncio.sleep(delay)
    finally:
        if out_file:
            out_file.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NHRM 純 Playwright 批次查詢")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--name", help="查詢單一姓名")
    group.add_argument("--jsonl", help="JSONL 檔路徑，每行含 name（與可選的 twtjdb_id）")
    parser.add_argument("--out", help="輸出 JSONL 路徑（支援斷點續跑）")
    parser.add_argument("--delay", type=float, default=1.0, help="每筆之間的延遲秒數（預設 1）")
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    if args.name:
        rows = [{"name": args.name}]
    elif args.jsonl:
        with open(args.jsonl, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))

    out_path = Path(args.out) if args.out else None
    asyncio.run(run_batch(rows, out_path, args.delay))
