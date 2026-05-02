#!/usr/bin/env python3
"""
臺灣轉型正義資料庫：已跑過管線的 **twtjdb 資料列 id** 登錄（JSONL，預設在 gitignore 的 private/）。

避免同人多案重複耗 API：合併素材時請用與匯出腳本相同的「同人多案」解析，一次登錄該次素材所含的全部 id。

環境變數（選用）：
  TWTJDB_RUN_REGISTRY=/path/to/file.jsonl

指令：
  python scripts/gemini/twtjdb_run_registry.py list
  python scripts/gemini/twtjdb_run_registry.py check --find-id 11947
  python scripts/gemini/twtjdb_run_registry.py record --find-id 11947 --run-dir scripts/gemini/pipeline/runs/run-...
  python scripts/gemini/twtjdb_run_registry.py record --ids 11929,11947 --run-dir ...
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import REPO_ROOT
from twtjdb_row import (
    DEFAULT_XLSX,
    collect_merge_siblings,
    extract_by_excel_row,
    find_row_by_id,
    row_to_dict,
)


def default_registry_path() -> Path:
    env = os.environ.get("TWTJDB_RUN_REGISTRY", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return (
        REPO_ROOT
        / "scripts"
        / "gemini"
        / "private"
        / "twtjdb_processed_ids.jsonl"
    )


def load_registered_ids(registry: Path) -> set[str]:
    if not registry.is_file():
        return set()
    out: set[str] = set()
    for line in registry.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        ids = obj.get("twtjdb_ids")
        if isinstance(ids, list):
            for x in ids:
                s = str(x).strip()
                if s:
                    out.add(s)
    return out


def append_registry_batch(
    registry: Path,
    twtjdb_ids: list[str],
    *,
    run_dir: str | None,
    note: str,
    source: str,
) -> None:
    registry.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "twtjdb_ids": sorted(set(twtjdb_ids), key=lambda x: int(x) if str(x).isdigit() else 0),
        "run_dir": run_dir or "",
        "note": note,
        "source": source,
    }
    with registry.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _parse_ids_csv(s: str | None) -> list[str]:
    if not s or not str(s).strip():
        return []
    return [p.strip() for p in str(s).split(",") if p.strip()]


def resolve_merged_twtjdb_ids(xlsx: Path, find_id: str) -> list[str]:
    excel_row = find_row_by_id(xlsx, find_id)
    header, data = extract_by_excel_row(xlsx, excel_row)
    flat = row_to_dict(header, data)
    sibs = collect_merge_siblings(xlsx, excel_row, flat)
    ids: list[str] = []
    for _, fl in sibs:
        rid = fl.get("id")
        if rid is not None and str(rid).strip():
            ids.append(str(rid).strip())
    return ids


def ids_for_check_or_record(
    *,
    xlsx: Path,
    find_id: str | None,
    ids_csv: str | None,
    no_resolve_siblings: bool,
) -> list[str]:
    if find_id:
        fid = find_id.strip()
        if no_resolve_siblings:
            return [fid]
        if not xlsx.is_file():
            print(f"找不到 xlsx：{xlsx}", file=sys.stderr)
            raise SystemExit(2)
        return resolve_merged_twtjdb_ids(xlsx, fid)
    raw = _parse_ids_csv(ids_csv)
    if not raw:
        print("請提供 --find-id 或 --ids。", file=sys.stderr)
        raise SystemExit(2)
    return raw


def check_overlap(
    merged: list[str],
    registered: set[str],
) -> tuple[str, int]:
    """
    回傳 (訊息, exit_code)。
    exit 0：無重疊；1：部分重疊；2：merged 全數已登錄。
    """
    mset = set(merged)
    inter = mset & registered
    if not inter:
        return ("尚未登錄（與 registry 無重疊）。", 0)
    if inter == mset:
        return (
            f"此批 id 已全部登錄過：{sorted(inter, key=lambda x: int(x) if x.isdigit() else 0)}",
            2,
        )
    return (
        f"部分 id 已登錄：{sorted(inter, key=lambda x: int(x) if x.isdigit() else 0)}；"
        f"未登錄：{sorted(mset - inter, key=lambda x: int(x) if x.isdigit() else 0)}",
        1,
    )


def record_batch_after_pipeline(
    *,
    registry: Path | None,
    find_id: str | None,
    ids_csv: str | None,
    no_resolve_siblings: bool,
    xlsx: Path,
    run_dir: Path,
    note: str,
) -> None:
    if not find_id and not (ids_csv and str(ids_csv).strip()):
        return
    path = registry or default_registry_path()
    if find_id:
        ids = ids_for_check_or_record(
            xlsx=xlsx,
            find_id=find_id.strip(),
            ids_csv=None,
            no_resolve_siblings=no_resolve_siblings,
        )
    else:
        ids = _parse_ids_csv(ids_csv)
    append_registry_batch(
        path,
        ids,
        run_dir=str(run_dir.resolve()),
        note=note,
        source="pipeline",
    )
    print(
        f"[twtjdb_run_registry] 已登錄 twtjdb id：{', '.join(ids)} → {path}",
        file=sys.stderr,
    )


def _cmd_list(registry: Path) -> None:
    reg = load_registered_ids(registry)
    if not reg:
        print("(registry 無資料或檔案不存在)")
        return
    for x in sorted(reg, key=lambda s: int(s) if s.isdigit() else 0):
        print(x)


def _cmd_check(args: argparse.Namespace) -> None:
    xlsx: Path = args.xlsx.resolve()
    if args.find_id:
        if not args.no_resolve_siblings and not xlsx.is_file():
            print(f"找不到 xlsx：{xlsx}", file=sys.stderr)
            raise SystemExit(2)
        merged = ids_for_check_or_record(
            xlsx=xlsx,
            find_id=args.find_id,
            ids_csv=None,
            no_resolve_siblings=args.no_resolve_siblings,
        )
    elif args.ids:
        merged = _parse_ids_csv(args.ids)
    else:
        print("請提供 --find-id 或 --ids。", file=sys.stderr)
        raise SystemExit(2)
    reg = load_registered_ids(args.registry)
    msg, code = check_overlap(merged, reg)
    print(f"本批 id：{', '.join(merged)}")
    print(msg)
    raise SystemExit(code)


def _cmd_record(args: argparse.Namespace) -> None:
    xlsx: Path = args.xlsx.resolve()
    if args.find_id:
        if not args.no_resolve_siblings and not xlsx.is_file():
            print(f"找不到 xlsx：{xlsx}", file=sys.stderr)
            raise SystemExit(2)
        merged = ids_for_check_or_record(
            xlsx=xlsx,
            find_id=args.find_id,
            ids_csv=None,
            no_resolve_siblings=args.no_resolve_siblings,
        )
    elif args.ids:
        merged = _parse_ids_csv(args.ids)
    else:
        print("請提供 --find-id 或 --ids。", file=sys.stderr)
        raise SystemExit(2)
    reg = load_registered_ids(args.registry)
    _, code = check_overlap(merged, reg)
    if code == 2 and not args.force:
        print(
            "此批 id 已全部登錄過；略過寫入。若要再寫一筆紀錄請加 --force。",
            file=sys.stderr,
        )
        return
    append_registry_batch(
        args.registry,
        merged,
        run_dir=args.run_dir or "",
        note=args.note or "",
        source="cli_record",
    )
    print(f"已寫入 {len(merged)} 個 id → {args.registry}", file=sys.stderr)


def main() -> None:
    p = argparse.ArgumentParser(description="twtjdb 管線已跑 id 登錄／檢查")
    p.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="JSONL 路徑（預設 private/twtjdb_processed_ids.jsonl 或環境變數 TWTJDB_RUN_REGISTRY）",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("list", help="列出已登錄的 id（聯集）")
    sp.set_defaults(func=lambda a: _cmd_list(a.registry or default_registry_path()))

    sc = sub.add_parser("check", help="檢查本批 id 是否已登錄（會解析同人多案）")
    gcx = sc.add_mutually_exclusive_group(required=True)
    gcx.add_argument("--find-id", metavar="ID", default=None)
    gcx.add_argument("--ids", metavar="CSV", default=None, help="逗號分隔")
    sc.add_argument(
        "--no-resolve-siblings",
        action="store_true",
        help="僅檢查單一 id，不掃描全檔合併同人列",
    )
    sc.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    sc.set_defaults(func=_cmd_check)

    sr = sub.add_parser("record", help="手動寫入一筆登錄")
    grx = sr.add_mutually_exclusive_group(required=True)
    grx.add_argument("--find-id", metavar="ID", default=None)
    grx.add_argument("--ids", metavar="CSV", default=None)
    sr.add_argument("--no-resolve-siblings", action="store_true")
    sr.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    sr.add_argument("--run-dir", metavar="PATH", default="", help="對應 pipeline 輸出目錄")
    sr.add_argument("--note", default="", help="備註")
    sr.add_argument(
        "--force",
        action="store_true",
        help="即使本批 id 已全部登錄過仍再寫一筆",
    )
    sr.set_defaults(func=_cmd_record)

    args = p.parse_args()
    if args.registry is None:
        args.registry = default_registry_path()
    args.registry = args.registry.expanduser().resolve()

    fn: Any = args.func
    fn(args)


if __name__ == "__main__":
    main()
