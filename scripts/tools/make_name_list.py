"""
從 twtjdb JSON 產生給 nhrm_researcher 用的名單 JSONL。

用法：
    # 有座標的 821 筆
    python make_name_list.py --source map_ready > names_map_ready.jsonl

    # 無座標的 14125 筆（量大，建議先取前 N 筆測試）
    python make_name_list.py --source pending --limit 50 > names_pending_50.jsonl
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "processed"

SOURCES = {
    "map_ready": DATA_DIR / "twtjdb_map_ready.json",
    "pending": DATA_DIR / "twtjdb_pending.json",
}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=list(SOURCES), default="map_ready")
    parser.add_argument("--limit", type=int, default=None, help="只取前 N 筆")
    args = parser.parse_args()

    path = SOURCES[args.source]
    with open(path, encoding="utf-8") as f:
        persons = json.load(f)["persons"]

    if args.limit:
        persons = persons[: args.limit]

    for p in persons:
        name = p.get("name", "").strip()
        if not name:
            continue
        row = {"twtjdb_id": p["id"], "name": name}
        print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
