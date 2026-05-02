#!/usr/bin/env python3
"""
將臺灣轉型正義資料庫 xlsx **每一筆資料列** 各匯出一組 .json + .md
（內容格式與 `twtjdb_structured.py` 單列相同）。

單次開檔、串流逐列，適合約 1.5 萬筆；勿對每列呼叫 `extract_by_excel_row`（會重複開檔極慢）。

  python scripts/gemini/twtjdb_export_all.py --out-dir scripts/gemini/private/twtjdb_all

產物：
  OUT_DIR/index.jsonl     每行一筆 {"excel_row","twtjdb_id","base"}
  OUT_DIR/<base>.json     與單列 structured 相同 schema
  OUT_DIR/<base>.md

建議輸出到已 gitignore 的目錄；全量約 3 萬個檔案，體積可能數 GB。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from twtjdb_encoding_catalog import DEFAULT_ENCODING_XLSX, load_field_encoding_catalog, subset_for_flat
from twtjdb_row import (
    DEFAULT_XLSX,
    REPO_ROOT,
    TWTJDB_NOTES_FOR_AGENTS_SEMANTICS,
    group_by_field_prefix,
    iter_all_data_rows,
)
from twtjdb_structured import build_main_table_rows, render_markdown


def safe_filename_part(s: str, *, max_len: int = 120) -> str:
    t = re.sub(r"[\s\\/:*?\"<>|\x00-\x1f]+", "_", str(s).strip()) or "unknown"
    return t[:max_len]


def main() -> None:
    p = argparse.ArgumentParser(description="twtjdb xlsx 全表 → 每筆 json+md")
    p.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX, help="資料庫 xlsx")
    p.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        metavar="DIR",
        help="輸出目錄（會建立）",
    )
    p.add_argument(
        "--max-main-rows",
        type=int,
        default=800,
        metavar="N",
        help="主表最多列數（0=不限制）；與 twtjdb_structured 相同",
    )
    p.add_argument(
        "--limit",
        type=int,
        metavar="N",
        default=0,
        help="僅處理前 N 筆非空列（0=全表，試跑可用 --limit 50）",
    )
    p.add_argument(
        "--skip-existing",
        action="store_true",
        help="若 <base>.json 已存在則跳過該筆",
    )
    p.add_argument(
        "--encoding-xlsx",
        type=Path,
        default=None,
        metavar="PATH",
        help="《編碼說明》xlsx（預設同 twtjdb_structured）",
    )
    p.add_argument(
        "--no-encoding-doc",
        action="store_true",
        help="不讀編碼說明",
    )
    args = p.parse_args()

    xlsx = args.xlsx.resolve()
    if not xlsx.is_file():
        print(f"找不到檔案：{xlsx}", file=sys.stderr)
        raise SystemExit(1)

    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "index.jsonl"

    enc_path = (
        args.encoding_xlsx.resolve()
        if args.encoding_xlsx
        else DEFAULT_ENCODING_XLSX.resolve()
    )
    field_catalog: dict[str, dict[str, str]] = {}
    if not args.no_encoding_doc:
        field_catalog = load_field_encoding_catalog(enc_path)
    try:
        enc_display = str(enc_path.relative_to(REPO_ROOT))
    except ValueError:
        enc_display = str(enc_path)

    try:
        rel = xlsx.relative_to(REPO_ROOT)
    except ValueError:
        rel = xlsx

    max_main = args.max_main_rows if args.max_main_rows > 0 else None
    used_bases: set[str] = set()
    n_done = 0
    n_skip = 0

    with index_path.open("w", encoding="utf-8") as index_f:

        def unique_base(raw: str, excel_row: int) -> str:
            b = raw
            if b not in used_bases:
                used_bases.add(b)
                return b
            b2 = f"{raw}_r{excel_row}"
            used_bases.add(b2)
            return b2

        for excel_row, flat in iter_all_data_rows(xlsx):
            if args.limit and n_done + n_skip >= args.limit:
                break

            rid = flat.get("id")
            raw_base = (
                safe_filename_part(str(rid))
                if rid is not None and str(rid).strip()
                else f"row_{excel_row}"
            )
            base = unique_base(raw_base, excel_row)
            json_path = out_dir / f"{base}.json"
            md_path = out_dir / f"{base}.md"

            if args.skip_existing and json_path.is_file():
                n_skip += 1
                rec = {
                    "excel_row": excel_row,
                    "twtjdb_id": str(rid) if rid is not None else "",
                    "base": base,
                    "skipped": True,
                }
                index_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                continue

            grouped = group_by_field_prefix(flat)
            main_rows, truncated = build_main_table_rows(
                flat, max_rows=max_main, field_catalog=field_catalog
            )

            meta = {
                "source_xlsx": str(rel),
                "excel_row": excel_row,
                "twtjdb_id": str(rid) if rid is not None else "",
                "export_tool": "twtjdb_export_all_v1",
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "encoding_doc_xlsx": enc_display,
                "encoding_doc_loaded": bool(field_catalog),
            }

            payload: dict[str, Any] = {
                "meta": meta,
                "flat_columns": flat,
                "grouped_by_prefix": grouped,
                "main_table_rows_draft": main_rows,
                "field_encoding_from_doc": subset_for_flat(flat, field_catalog),
                "notes_for_agents": (
                    "正規化值預留空字串，供 §2 填寫；"
                    "填寫狀態預設 provided 表示資料庫有值。"
                    "`field_encoding_from_doc` 來自《編碼說明》xlsx 自動解析。"
                    + TWTJDB_NOTES_FOR_AGENTS_SEMANTICS
                ),
            }

            json_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            md_path.write_text(
                render_markdown(meta, main_rows, grouped, truncated=truncated),
                encoding="utf-8",
            )

            rec = {
                "excel_row": excel_row,
                "twtjdb_id": str(rid) if rid is not None else "",
                "base": base,
                "skipped": False,
            }
            index_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n_done += 1

            if n_done % 500 == 0:
                print(f"[twtjdb_export_all] 已寫入 {n_done} 筆 …", file=sys.stderr)

    print(
        f"[twtjdb_export_all] 完成：新寫 {n_done} 筆，跳過 {n_skip} 筆，目錄：{out_dir}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
