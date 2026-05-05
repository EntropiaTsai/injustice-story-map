"""
從 twtjdb JSON 產生給 nhrm_batch 用的名單 JSONL。

用法：
    python make_name_list.py                        # 全部 14946 筆
    python make_name_list.py --source map_ready     # 有座標的 821 筆
    python make_name_list.py --source pending       # 無座標的 14125 筆
    python make_name_list.py --limit 50             # 只取前 50 筆（測試用）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "processed"

SOURCES = {
    "map_ready": DATA_DIR / "twtjdb_map_ready.json",
    "pending":   DATA_DIR / "twtjdb_pending.json",
}


def load_persons(source: str | None) -> list[dict]:
    if source:
        with open(SOURCES[source], encoding="utf-8") as f:
            return json.load(f)["persons"]
    # 全部：map_ready + pending
    persons = []
    for path in SOURCES.values():
        with open(path, encoding="utf-8") as f:
            persons.extend(json.load(f)["persons"])
    return persons


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=list(SOURCES), default=None,
                        help="不指定則輸出全部（map_ready + pending）")
    parser.add_argument("--limit", type=int, default=None, help="只取前 N 筆")
    args = parser.parse_args()

    persons = load_persons(args.source)
    if args.limit:
        persons = persons[:args.limit]

    print(f"共 {len(persons)} 筆", file=sys.stderr)

    for p in persons:
        name = p.get("name", "").strip()
        if not name:
            continue
        print(json.dumps({"twtjdb_id": p["id"], "name": name}, ensure_ascii=False))


if __name__ == "__main__":
    main()
