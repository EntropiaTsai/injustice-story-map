#!/usr/bin/env python3
"""
依管線邏輯組出下一棒 `call.py` 的 `--user` 檔（避免手動複製貼上）。

範例（§3，預設讀 private 下慣用檔名）：

  python scripts/gemini/compose_agent_user.py --round 3 \\
    -o scripts/gemini/private/user_03.txt

  python scripts/gemini/call.py \\
    --system docs/agents/prompts/system_03_history_sources.txt \\
    --user scripts/gemini/private/user_03.txt \\
    > scripts/gemini/private/out_03_history.md

慣用檔名（可 --s2 / --material 等覆寫）：
  case01.md, out_02_structuring.md, out_03_history.md, out_04_copy.md,
  out_05_geo.md, out_06_sensitivity.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PRIVATE = Path(__file__).resolve().parent / "private"


def _read(p: Path, label: str) -> str:
    if not p.is_file():
        print(f"找不到 {label}：{p}", file=sys.stderr)
        raise SystemExit(1)
    return p.read_text(encoding="utf-8").strip()


def build_s3(s2: str, material: str) -> str:
    return f"""請依 System 中的「台灣歷史資料學專員」角色產出完整輸出。

## 結構化專員（§2）產出
{s2}

## 原始素材（連結與補充對照用）
{material}
"""


def build_s4(s3: str, s2: str) -> str:
    return f"""請依 System 中的「文字編輯」角色產出完整輸出。

## 台灣歷史資料學專員（§3）產出
{s3}

## 結構化專員（§2）產出（欄位對照）
{s2}
"""


def build_s5(s2: str, s4: str) -> str:
    return f"""請依 System 中的「地理資訊專員」角色產出完整輸出。

## 結構化專員（§2）產出
{s2}

## 文字編輯（§4）產出
{s4}
"""


def build_s6(s2: str, s4: str) -> str:
    return f"""請依 System 中的「受難者權益及法務專員」角色產出完整輸出。

## 結構化專員（§2）產出
{s2}

## 文字編輯（§4）產出
{s4}
"""


def build_s7(s2: str, s4: str, s5: str, s6: str, cid: str) -> str:
    tail = cid.strip() or "（未指定 --contribution-id，請於 JSON 內用 placeholder）"
    return f"""請依 System 中的「UI 工程師」角色產出完整輸出（含 JSON 程式碼區塊與檢查清單）。

## 結構化專員（§2）產出
{s2}

## 文字編輯（§4）產出
{s4}

## 地理專員（§5）產出
{s5}

## 權益專員（§6）產出
{s6}

## 投稿／素材識別（供 meta）
{tail}
"""


def main() -> None:
    p = argparse.ArgumentParser(description="組出 gemini call 的 user 檔")
    p.add_argument(
        "--round",
        type=int,
        required=True,
        choices=(3, 4, 5, 6, 7),
        metavar="N",
        help="§3 … §7",
    )
    p.add_argument("-o", "--out", type=Path, required=True, help="輸出 user 檔路徑")
    p.add_argument("--s2", type=Path, help="§2 產出 .md（預設 private/out_02_structuring.md）")
    p.add_argument("--material", type=Path, help="原始素材（§3 用，預設 private/case01.md）")
    p.add_argument("--s3", type=Path, help="§3 產出（§4 用）")
    p.add_argument("--s4", type=Path, help="§4 產出（§5§6 用）")
    p.add_argument("--s5", type=Path, help="§5 產出（§7 用）")
    p.add_argument("--s6", type=Path, help="§6 產出（§7 用）")
    p.add_argument(
        "--contribution-id",
        help="§7 用投稿／素材 id（可選）",
    )
    args = p.parse_args()

    s2_path = args.s2 or PRIVATE / "out_02_structuring.md"
    mat_path = args.material or PRIVATE / "case01.md"

    if args.round == 3:
        text = build_s3(_read(s2_path, "§2 產出"), _read(mat_path, "原始素材"))
    elif args.round == 4:
        s3_path = args.s3 or PRIVATE / "out_03_history.md"
        text = build_s4(_read(s3_path, "§3 產出"), _read(s2_path, "§2 產出"))
    elif args.round == 5:
        s4_path = args.s4 or PRIVATE / "out_04_copy.md"
        text = build_s5(_read(s2_path, "§2 產出"), _read(s4_path, "§4 產出"))
    elif args.round == 6:
        s4_path = args.s4 or PRIVATE / "out_04_copy.md"
        text = build_s6(_read(s2_path, "§2 產出"), _read(s4_path, "§4 產出"))
    else:
        s4_path = args.s4 or PRIVATE / "out_04_copy.md"
        s5_path = args.s5 or PRIVATE / "out_05_geo.md"
        s6_path = args.s6 or PRIVATE / "out_06_sensitivity.md"
        text = build_s7(
            _read(s2_path, "§2 產出"),
            _read(s4_path, "§4 產出"),
            _read(s5_path, "§5 產出"),
            _read(s6_path, "§6 產出"),
            args.contribution_id or "",
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text + "\n", encoding="utf-8")
    print(f"已寫入：{args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
