#!/usr/bin/env python3
"""
從「臺灣轉型正義資料庫」xlsx **單一資料列** 匯出純文字，供 pipeline / call.py 使用。

預設資料檔（專案內）：
  data/reference/twtjdb/臺灣轉型正義資料庫(14946筆)_20220420.xlsx

範例：
  python scripts/gemini/material_from_twtjdb.py --row 2 --out scripts/gemini/private/material.txt
  python scripts/gemini/pipeline.py --input scripts/gemini/private/material.txt

依資料庫 id 尋列（由第 2 列起掃描，大檔可能較久）：
  python scripts/gemini/material_from_twtjdb.py --find-id 28797 --out scripts/gemini/private/material.txt

預設會掃描全檔：若同一人有多筆案件列（姓名核心、出生年、籍貫一致，如姓名末「一」「二」），合併為單一素材；只要單列請加 `--no-merge-siblings`。

若希望 **表格化 JSON + 主表 Markdown**（較利於 §2），請用：
  python scripts/gemini/twtjdb_structured.py --row 2 --out-base scripts/gemini/private/case01
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from twtjdb_encoding_catalog import DEFAULT_ENCODING_XLSX, load_field_encoding_catalog, render_flat_encoding_text
from twtjdb_row import (
    DEFAULT_XLSX,
    REPO_ROOT,
    collect_merge_siblings,
    extract_by_excel_row,
    find_row_by_id,
    row_to_dict,
    twtjdb_semantics_plaintext_block,
)


def row_to_text(
    flat: dict[str, object],
    *,
    max_field_len: int,
) -> str:
    lines: list[str] = []
    for key in sorted(flat.keys()):
        v = flat[key]
        s = str(v).strip()
        if len(s) > max_field_len:
            s = s[:max_field_len] + "…（已截斷）"
        lines.append(f"{key}: {s}")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(
        description="轉型正義資料庫 xlsx → 單列純文字素材",
    )
    p.add_argument(
        "--xlsx",
        type=Path,
        default=DEFAULT_XLSX,
        help="資料庫 xlsx 路徑",
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--row",
        type=int,
        metavar="N",
        help="Excel 列號（2=第一筆資料）",
    )
    g.add_argument(
        "--find-id",
        metavar="ID",
        help="依「id」欄位搜尋（由第 2 列起掃描）",
    )
    p.add_argument(
        "--out",
        type=Path,
        help="輸出檔（未給則印到 stdout）",
    )
    p.add_argument(
        "--max-total-chars",
        type=int,
        default=120_000,
        metavar="N",
        help="全文上限字元（避免超過模型上下文）",
    )
    p.add_argument(
        "--max-field-len",
        type=int,
        default=2000,
        metavar="N",
        help="單一欄位上限字元",
    )
    p.add_argument(
        "--encoding-xlsx",
        type=Path,
        default=None,
        metavar="PATH",
        help="《編碼說明》xlsx（預設 data/reference/twtjdb/…編碼說明…）",
    )
    p.add_argument(
        "--no-encoding-doc",
        action="store_true",
        help="不附欄位說明附錄",
    )
    p.add_argument(
        "--no-merge-siblings",
        action="store_true",
        help="不掃描全檔；僅輸出錨點該列（關閉同人多案合併）",
    )
    args = p.parse_args()

    xlsx: Path = args.xlsx.resolve()
    if not xlsx.is_file():
        print(f"找不到檔案：{xlsx}", file=sys.stderr)
        raise SystemExit(1)

    if args.find_id is not None:
        excel_row = find_row_by_id(xlsx, args.find_id)
        print(f"[material_from_twtjdb] 找到 id，Excel 列號：{excel_row}", file=sys.stderr)
    else:
        excel_row = args.row
        assert excel_row is not None

    header, data = extract_by_excel_row(xlsx, excel_row)
    flat = row_to_dict(header, data)

    if args.no_merge_siblings:
        sibling_rows: list[tuple[int, dict[str, object]]] = [(excel_row, flat)]
    else:
        sibling_rows = collect_merge_siblings(xlsx, excel_row, flat)
        if len(sibling_rows) > 1:
            ids = [str(s[1].get("id", "")) for s in sibling_rows]
            print(
                "[material_from_twtjdb] 偵測到同人 "
                f"{len(sibling_rows)} 筆案件列，已合併輸出（id：{', '.join(ids)}）",
                file=sys.stderr,
            )

    body_parts: list[str] = []
    for i, (erow, fl) in enumerate(sibling_rows, start=1):
        rid = fl.get("id", "")
        block = row_to_text(fl, max_field_len=args.max_field_len)
        body_parts.append(
            f"────────\n【第 {i}/{len(sibling_rows)} 筆 · 資料列 id={rid} · Excel 列號={erow}】\n────────\n"
            + block
        )
    body = "\n\n".join(body_parts)

    encoding_append = ""
    if not args.no_encoding_doc:
        enc_path = (
            args.encoding_xlsx.resolve()
            if args.encoding_xlsx
            else DEFAULT_ENCODING_XLSX.resolve()
        )
        catalog = load_field_encoding_catalog(enc_path)
        if catalog:
            encoding_append = "\n" + render_flat_encoding_text(flat, catalog)
        else:
            print(
                "[material_from_twtjdb] 未載入編碼說明（檔案不存在或為空）："
                + str(enc_path),
                file=sys.stderr,
            )

    try:
        path_shown = xlsx.relative_to(REPO_ROOT)
    except ValueError:
        path_shown = xlsx
    merge_note = (
        f"同人合併：共 {len(sibling_rows)} 筆案件列（依姓名核心、出生年、籍貫比對）。"
        if len(sibling_rows) > 1
        else "單列匯出。"
    )
    intro = f"""【資料來源】
檔案：{path_shown}
錨點 Excel 列號：{excel_row}
{merge_note}
說明：以下由資料庫表單匯出為欄位名（多為英文代碼）與值；多筆時每段標明資料列 id 與列號。文末附《編碼說明》xlsx 自動解析之**欄位中文標題與說明**（可用 `--no-encoding-doc` 關閉）；若檔案缺失則僅有此文字提示。

{twtjdb_semantics_plaintext_block()}【欄位內容】
"""
    text = intro + body + encoding_append
    if len(text) > args.max_total_chars:
        text = text[: args.max_total_chars] + "\n\n…（全文已達 --max-total-chars 上限並截斷）\n"

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"已寫入：{args.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
