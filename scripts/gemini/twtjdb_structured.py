#!/usr/bin/env python3
"""
將臺灣轉型正義資料庫 xlsx **單列** 匯成：
  - JSON（機讀、分組）
  - Markdown（含 §2 可用的「主表」草稿）

預設會掃描全檔，若同一人有多筆案件列（姓名核心、出生年、籍貫一致），JSON 會附 `twtjdb_merged_cases`，Markdown 依時序分段；只要單列請加 `--no-merge-siblings`。

比純 key-value 敘述更利於「資料結構化專員」精修欄位。

  python scripts/gemini/twtjdb_structured.py --row 2 --out-base scripts/gemini/private/case01

**整份 xlsx 每筆各匯一組 json+md**（約 1.5 萬筆）請用 `twtjdb_export_all.py`（單次掃描，勿對每列重複開檔）。

會產生 case01.json、case01.md。若只要餵 §2，可將 .md 或其中「主表」段落貼為 User；
若跑全管線，可把 .md 當 pipeline --input（PM 仍會先看到表格化素材）。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from twtjdb_encoding_catalog import (
    DEFAULT_ENCODING_XLSX,
    load_field_encoding_catalog,
    subset_for_flat,
    truncate_for_table_note,
)
from twtjdb_row import (
    DEFAULT_XLSX,
    REPO_ROOT,
    TWTJDB_NOTES_FOR_AGENTS_SEMANTICS,
    collect_merge_siblings,
    extract_by_excel_row,
    find_row_by_id,
    group_by_field_prefix,
    row_to_dict,
    twtjdb_semantics_md_lines,
)

# 常見欄位 → 主表「項目」欄顯示用中文（其餘仍用英文代碼作項目名）
FIELD_LABELS: dict[str, str] = {
    "id": "資料庫 id",
    "name": "姓名（見「資料庫慣例」：占位符與頓號）",
    "gender": "性別",
    "birth_h": "出生年（欄位定義見編碼說明）",
    "province": "籍貫（省）— 非案發地",
    "city": "籍貫（縣市）— 非案發地",
    "edu": "教育程度",
    "occupation": "職業",
    "age": "年齡（紀錄當時）",
    "d1_authority": "機關（d1）",
    "d1_num": "案號／文號",
}


def _cell_md(s: str) -> str:
    t = s.replace("\r\n", " ").replace("\n", " ").replace("|", "／")
    if len(t) > 500:
        t = t[:500] + "…"
    return t


def build_main_table_rows(
    flat: dict[str, Any],
    *,
    max_rows: int | None,
    field_catalog: dict[str, dict[str, str]] | None = None,
) -> tuple[list[dict[str, str]], bool]:
    """產出與 OUTPUT_SCHEMAS / §2 主表概念對齊的列。"""
    cat = field_catalog or {}
    rows: list[dict[str, str]] = []
    truncated = False
    keys = sorted(flat.keys())
    for i, key in enumerate(keys):
        if max_rows is not None and i >= max_rows:
            truncated = True
            break
        raw = flat[key]
        spec = cat.get(key)
        if spec:
            label = spec.get("label_zh") or FIELD_LABELS.get(key, key)
        else:
            label = FIELD_LABELS.get(key, key)
        if key == "name":
            notes = (
                "來自轉型正義資料庫；語意請對照《編碼說明》。"
                "僅「－」等符號＝未載明占位（匯出或已改寫）；"
                "「、」後為別名或檔案通用字，非第二人。"
            )
        elif key in ("province", "city"):
            notes = (
                "來自轉型正義資料庫；語意請對照《編碼說明》。"
                "此欄為**籍貫**脈絡，**勿**當成事件發生地／拘捕地／法院地；"
                "地圖用「故事地點」請另欄標示或標待補。"
            )
        else:
            notes = "來自轉型正義資料庫；語意請對照《編碼說明》"
        if spec and spec.get("description"):
            notes = notes + "｜編碼說明摘要：" + truncate_for_table_note(spec["description"])
        rows.append(
            {
                "field": key,
                "field_label": label,
                "raw_from_submission": str(raw),
                "normalized_value": "",
                "fill_status": "provided",
                "notes": notes,
            }
        )
    return rows, truncated


def _md_main_table_block(
    main_rows: list[dict[str, str]],
    *,
    truncated: bool,
) -> list[str]:
    lines: list[str] = ["", "## 主表（草稿）", ""]
    lines.append(
        "| 項目 | 原始值（資料庫） | 正規化值 | 填寫狀態 | 備註（欄位代碼） |",
    )
    lines.append("|------|------------------|----------|----------|------------------|")
    for r in main_rows:
        item = _cell_md(r["field_label"])
        raw = _cell_md(r["raw_from_submission"])
        norm = _cell_md(r["normalized_value"] or "（請補）")
        status = r["fill_status"]
        note = _cell_md(f"{r['notes']} `{r['field']}`")
        lines.append(f"| {item} | {raw} | {norm} | {status} | {note} |")
    if truncated:
        lines.extend(
            [
                "",
                "> 主表列數已截斷；**完整欄位**見同檔 `.json` 對應 `flat_columns` 或 `twtjdb_merged_cases`。",
            ]
        )
    return lines


def _md_grouped_block(grouped: dict[str, dict[str, Any]]) -> list[str]:
    lines: list[str] = ["", "## 依欄位前綴分組（備查）", ""]
    for gname, gdict in grouped.items():
        title = "基本與未分類" if gname == "_base" else f"前綴 `{gname}_*`"
        lines.append(f"### {title}")
        lines.append("")
        lines.append("| 欄位 | 值 |")
        lines.append("|------|-----|")
        for k in sorted(gdict.keys()):
            lines.append(f"| `{k}` | {_cell_md(str(gdict[k]))} |")
        lines.append("")
    return lines


def render_markdown(
    meta: dict[str, Any],
    main_rows: list[dict[str, str]],
    grouped: dict[str, dict[str, Any]],
    *,
    truncated: bool,
    heading: str = "# 臺灣轉型正義資料庫 · 單筆結構化匯出",
) -> str:
    lines: list[str] = [
        heading,
        "",
        "## 給資料結構化專員（§2）",
        "",
        "以下由 **`twtjdb_structured.py`** 自表格轉成主表草稿（非最終定稿）。請你：",
        "",
        "1. 主表「項目」欄已盡可能帶入《臺灣轉型正義資料庫編碼說明》xlsx 內之**中文標題**；**完整逐欄說明**見同筆 JSON 的 `field_encoding_from_doc`。請依之補齊 **正規化值**、標註 **需澄清**。",
        "2. 合併同義欄位、刪減對本專案故事頁無用之冗餘代碼欄（於備註說明）。",
        "3. 勿臆測未出現在原始值中的史實。",
        "",
        *twtjdb_semantics_md_lines(),
        "## Meta",
        "",
    ]
    for k, v in meta.items():
        lines.append(f"- **{k}**：{v}")
    lines.extend(_md_main_table_block(main_rows, truncated=truncated))
    lines.extend(_md_grouped_block(grouped))
    return "\n".join(lines).rstrip() + "\n"


def render_merged_followup_section(
    case_index: int,
    total: int,
    twtjdb_id: str,
    excel_row: int,
    main_rows: list[dict[str, str]],
    grouped: dict[str, dict[str, Any]],
    *,
    truncated: bool,
) -> str:
    """錨點以外之同人案件列：接續 Markdown 區塊。"""
    lines: list[str] = [
        "",
        f"# 同人第 {case_index}/{total} 筆 · 資料列 id={twtjdb_id} · Excel 列號={excel_row}",
        "",
        "（與首段為同一身分鍵比對之另一案件列；請與 §2 一併結構化，注意多案時間線與法條差異。）",
    ]
    lines.extend(_md_main_table_block(main_rows, truncated=truncated))
    lines.extend(_md_grouped_block(grouped))
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    p = argparse.ArgumentParser(
        description="twtjdb 單列 → JSON + Markdown（結構化主表草稿）",
    )
    p.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX, help="資料庫 xlsx")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--row", type=int, metavar="N", help="Excel 列號（2=第一筆資料）")
    g.add_argument("--find-id", dest="find_id", metavar="ID", help="依 id 搜尋列")
    p.add_argument(
        "--out-base",
        type=Path,
        required=True,
        metavar="PATH",
        help="輸出檔基底路徑（不含副檔名），會寫 PATH.json 與 PATH.md",
    )
    p.add_argument(
        "--max-main-rows",
        type=int,
        default=800,
        metavar="N",
        help="主表最多列數；超出的欄位仍完整保留於 JSON（0 表示不限制）",
    )
    p.add_argument(
        "--encoding-xlsx",
        type=Path,
        default=None,
        metavar="PATH",
        help="《編碼說明》xlsx（預設 data/reference/twtjdb/臺灣轉型正義資料庫編碼說明_20210226.xlsx）",
    )
    p.add_argument(
        "--no-encoding-doc",
        action="store_true",
        help="不讀編碼說明、不寫 field_encoding_from_doc",
    )
    p.add_argument(
        "--no-merge-siblings",
        action="store_true",
        help="不掃描全檔合併同人其他案件列（僅輸出錨點該列）",
    )
    args = p.parse_args()

    xlsx = args.xlsx.resolve()
    if not xlsx.is_file():
        print(f"找不到檔案：{xlsx}", file=sys.stderr)
        raise SystemExit(1)

    if args.find_id is not None:
        excel_row = find_row_by_id(xlsx, args.find_id)
        print(f"[twtjdb_structured] Excel 列號：{excel_row}", file=sys.stderr)
    else:
        excel_row = args.row

    header, data = extract_by_excel_row(xlsx, excel_row)
    flat = row_to_dict(header, data)

    if args.no_merge_siblings:
        sibling_rows: list[tuple[int, dict[str, Any]]] = [(excel_row, flat)]
    else:
        sibling_rows = collect_merge_siblings(xlsx, excel_row, flat)
        if len(sibling_rows) > 1:
            ids = [str(s[1].get("id", "")) for s in sibling_rows]
            print(
                "[twtjdb_structured] 偵測到同人 "
                f"{len(sibling_rows)} 筆案件列，已合併輸出（id：{', '.join(ids)}）",
                file=sys.stderr,
            )

    grouped = group_by_field_prefix(flat)

    field_catalog: dict[str, dict[str, str]] = {}
    if not args.no_encoding_doc:
        enc_path = (
            args.encoding_xlsx.resolve()
            if args.encoding_xlsx
            else DEFAULT_ENCODING_XLSX.resolve()
        )
        field_catalog = load_field_encoding_catalog(enc_path)

    max_main = args.max_main_rows if args.max_main_rows > 0 else None
    main_rows, truncated = build_main_table_rows(
        flat, max_rows=max_main, field_catalog=field_catalog
    )

    try:
        rel = xlsx.relative_to(REPO_ROOT)
    except ValueError:
        rel = xlsx

    enc_path = (
        args.encoding_xlsx.resolve()
        if args.encoding_xlsx
        else DEFAULT_ENCODING_XLSX.resolve()
    )
    try:
        enc_display = str(enc_path.relative_to(REPO_ROOT))
    except ValueError:
        enc_display = str(enc_path)

    rid = flat.get("id", "")
    meta: dict[str, Any] = {
        "source_xlsx": str(rel),
        "excel_row": excel_row,
        "twtjdb_id": str(rid) if rid is not None else "",
        "export_tool": "twtjdb_structured_v1",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "encoding_doc_xlsx": enc_display,
        "encoding_doc_loaded": bool(field_catalog),
    }
    if len(sibling_rows) > 1:
        meta["merge_sibling_count"] = len(sibling_rows)
        meta["anchor_twtjdb_id"] = str(rid) if rid is not None else ""
        meta["merged_twtjdb_ids_chronological"] = [
            str(s[1].get("id", "")) for s in sibling_rows
        ]

    twtjdb_merged_cases: list[dict[str, Any]] | None = None
    if len(sibling_rows) > 1:
        twtjdb_merged_cases = []
        for erow_m, fl_m in sibling_rows:
            gm = group_by_field_prefix(fl_m)
            mm, tm = build_main_table_rows(
                fl_m, max_rows=max_main, field_catalog=field_catalog
            )
            twtjdb_merged_cases.append(
                {
                    "twtjdb_id": str(fl_m.get("id", "")),
                    "excel_row": erow_m,
                    "flat_columns": fl_m,
                    "grouped_by_prefix": gm,
                    "main_table_rows_draft": mm,
                    "main_table_truncated": tm,
                }
            )

    notes_tail = (
        "若 `twtjdb_merged_cases` 含多筆，為同人依時序（d1_y、id）排序之各案件列，"
        "請一併結構化；地圖主軸若只取一案，以 `meta.anchor_twtjdb_id` 對應之列為準。"
        if twtjdb_merged_cases
        else ""
    )

    payload: dict[str, Any] = {
        "meta": meta,
        "flat_columns": flat,
        "grouped_by_prefix": grouped,
        "main_table_rows_draft": main_rows,
        "field_encoding_from_doc": subset_for_flat(flat, field_catalog),
        "notes_for_agents": (
            "正規化值預留空字串，供 §2 填寫；"
            "填寫狀態預設 provided 表示資料庫有值。"
            "`field_encoding_from_doc` 來自《編碼說明》xlsx 自動解析，與主表「項目」中文標題一致。"
            + notes_tail
            + TWTJDB_NOTES_FOR_AGENTS_SEMANTICS
        ),
    }
    if twtjdb_merged_cases is not None:
        payload["twtjdb_merged_cases"] = twtjdb_merged_cases

    base = args.out_base.expanduser()
    base.parent.mkdir(parents=True, exist_ok=True)
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")

    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if len(sibling_rows) > 1:
        h = f"# 臺灣轉型正義資料庫 · 結構化匯出（同人 {len(sibling_rows)} 筆案件列）"
        er0, fl0 = sibling_rows[0]
        g0 = group_by_field_prefix(fl0)
        m0, t0 = build_main_table_rows(
            fl0, max_rows=max_main, field_catalog=field_catalog
        )
        md_body = render_markdown(
            meta, m0, g0, truncated=t0, heading=h
        )
        for idx in range(1, len(sibling_rows)):
            er_m, fl_m = sibling_rows[idx]
            gm = group_by_field_prefix(fl_m)
            mm, tm = build_main_table_rows(
                fl_m, max_rows=max_main, field_catalog=field_catalog
            )
            md_body += render_merged_followup_section(
                idx + 1,
                len(sibling_rows),
                str(fl_m.get("id", "")),
                er_m,
                mm,
                gm,
                truncated=tm,
            )
    else:
        md_body = render_markdown(meta, main_rows, grouped, truncated=truncated)

    md_path.write_text(md_body, encoding="utf-8")
    print(f"已寫入：{json_path}", file=sys.stderr)
    print(f"已寫入：{md_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
