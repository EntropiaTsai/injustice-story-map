#!/usr/bin/env python3
"""
從 nhrm_merged.json 匯出單筆受難者資料為純文字，供 pipeline.py 使用。

範例：
  python scripts/gemini/material_from_nhrm.py --id 3939
  python scripts/gemini/material_from_nhrm.py --id 3939 --out scripts/gemini/private/material.txt
  python scripts/gemini/pipeline.py --input scripts/gemini/private/material.txt

搜尋姓名（回傳第一筆）：
  python scripts/gemini/material_from_nhrm.py --name 童常
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from config import REPO_ROOT

NHRM_MERGED = REPO_ROOT / "data" / "processed" / "nhrm_merged.json"

ROC_OFFSET = 1911


def _roc_to_western(year_roc: int | None) -> str:
    if year_roc is None:
        return ""
    return f"民國{year_roc}年（{year_roc + ROC_OFFSET}年）"


def _load_index(path: Path) -> dict[int, dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {p["nhrm_id"]: p for p in data["persons"]}


def format_person(p: dict) -> str:
    lines: list[str] = []

    def sec(title: str) -> None:
        lines.append(f"\n## {title}")

    def row(label: str, value: object) -> None:
        v = str(value).strip() if value is not None else ""
        if v:
            lines.append(f"{label}：{v}")

    # ── 標頭 ──────────────────────────────────────────────────────────────────
    lines.append("【資料來源】")
    lines.append(f"檔案：data/processed/nhrm_merged.json")
    lines.append(f"nhrm_id：{p['nhrm_id']}")
    if p.get("twtjdb_id"):
        lines.append(f"twtjdb_id：{p['twtjdb_id']}")
    lines.append(f"NHRM 頁面：{p.get('nhrm_url') or ''}")
    lines.append("")

    # ── 基本資料 ──────────────────────────────────────────────────────────────
    sec("基本資料")
    row("姓名", p.get("name"))
    row("別名／字號", p.get("nickname"))
    row("性別", p.get("gender"))
    birth = p.get("birth_year") or ""
    death = p.get("death_year") or ""
    if birth or death:
        row("生卒年", f"{birth} – {death}" if death else birth)
    row("籍貫省份", p.get("province"))
    row("籍貫縣市", p.get("city"))
    row("案發相關地點", p.get("place"))

    # ── 刑罰（NHRM 記錄） ─────────────────────────────────────────────────────
    nhrm_penalty = p.get("nhrm_penalty") or []
    if nhrm_penalty:
        sec("刑事記錄（NHRM）")
        for i, pen in enumerate(nhrm_penalty, 1):
            prefix = f"  [{i}]"
            year = pen.get("judg_year_roc")
            no = pen.get("judg_no") or ""
            occ = pen.get("occupation") or ""
            judg = pen.get("judgment") or ""
            term = pen.get("term") or pen.get("penalty_text") or ""
            lines.append(f"{prefix} 案號：{no}")
            if year:
                lines.append(f"       裁判年：{_roc_to_western(int(year))}")
            if occ:
                lines.append(f"       職務：{occ}")
            if judg:
                lines.append(f"       罪名：{judg}")
            if term:
                lines.append(f"       刑期：{term}")

    # ── 終審判決（twtjdb 結構化） ─────────────────────────────────────────────
    j = p.get("judgment")
    if j:
        sec("終審判決（twtjdb 結構化資料）")
        row("裁判機關", j.get("authority"))
        row("裁判年度", _roc_to_western(j.get("year_roc")))
        row("刑罰", j.get("penalty_text"))
        row("死刑", "是" if j.get("has_death_penalty") else None)
        row("無期徒刑", "是" if j.get("has_life_sentence") else None)
        # 移除書名前綴與「匪」字（與 StorySidebar 邏輯一致）
        org_raw = j.get("organization") or ""
        org_cleaned = org_raw.replace("歷年辦理匪案彙編：", "").replace("歷年辦理匪案彙編:", "")
        if org_cleaned.startswith("匪"):
            org_cleaned = org_cleaned[1:]
        if org_cleaned not in ("暫無資料", "不詳", ""):
            row("所屬組織", org_cleaned)

    # ── 傳記 ──────────────────────────────────────────────────────────────────
    intro = (p.get("introduction") or "").strip()
    if intro:
        sec("傳記／簡介")
        lines.append(intro)

    # ── 相關案件 ──────────────────────────────────────────────────────────────
    cases = p.get("cases") or []
    if cases:
        sec("相關案件")
        for c in cases:
            lines.append(f"  - {c.get('name') or c.get('id')}")

    # ── 相關人物 ──────────────────────────────────────────────────────────────
    related = p.get("related_persons") or []
    if related:
        # 去重
        seen: set[int] = set()
        unique_related = []
        for r in related:
            if r["nhrm_id"] not in seen:
                seen.add(r["nhrm_id"])
                unique_related.append(r)
        sec("同案相關人物")
        for r in unique_related:
            lines.append(f"  - {r['name']}（nhrm_id: {r['nhrm_id']}）")

    # ── 平復補償 ──────────────────────────────────────────────────────────────
    recoup = p.get("recoup") or []
    if recoup:
        sec("平復補償")
        for r in recoup:
            lines.append(f"  ✓ {r}")

    # ── 歷史文件 ──────────────────────────────────────────────────────────────
    docs = p.get("documents") or []
    if docs:
        sec(f"相關歷史文件（{len(docs)} 份）")
        for d in docs:
            title = d.get("title") or "(無標題)"
            auth = d.get("authority") or ""
            date = d.get("date") or ""
            meta = "、".join(x for x in [auth, date] if x)
            lines.append(f"  - {title}" + (f"（{meta}）" if meta else ""))

    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(description="NHRM merged JSON → 純文字素材")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--id", type=int, metavar="NHRM_ID", help="nhrm_id")
    g.add_argument("--name", metavar="NAME", help="姓名（回傳第一筆符合）")
    p.add_argument("--merged", type=Path, default=NHRM_MERGED, help="nhrm_merged.json 路徑")
    p.add_argument("--out", type=Path, help="輸出檔（未給則印到 stdout）")
    args = p.parse_args()

    if not args.merged.exists():
        print(f"找不到：{args.merged}", file=sys.stderr)
        print("請先執行 scripts/tools/merge_nhrm.py", file=sys.stderr)
        sys.exit(1)

    index = _load_index(args.merged)

    if args.id is not None:
        person = index.get(args.id)
        if person is None:
            print(f"nhrm_id {args.id} 不存在", file=sys.stderr)
            sys.exit(1)
    else:
        matched = [v for v in index.values() if args.name in (v.get("name") or "")]
        if not matched:
            print(f"找不到姓名「{args.name}」", file=sys.stderr)
            sys.exit(1)
        if len(matched) > 1:
            print(
                f"找到 {len(matched)} 筆，取第一筆（nhrm_id={matched[0]['nhrm_id']}）"
                f"。其他：{[m['nhrm_id'] for m in matched[1:]]}",
                file=sys.stderr,
            )
        person = matched[0]

    text = format_person(person)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"已寫入：{args.out}", file=sys.stderr)
    else:
        sys.stdout.write(text + "\n")


if __name__ == "__main__":
    main()
