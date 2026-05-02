#!/usr/bin/env python3
"""
檢查手動多輪時 private/ 慣用檔是否齊備；缺檔時印出建議指令（exit 1）。

  python scripts/gemini/check_private_inputs.py
  python scripts/gemini/check_private_inputs.py --expect-round 4
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PRIVATE = Path(__file__).resolve().parent / "private"

# round N 需要「上一棒」已存在
REQUIRES: dict[int, list[str]] = {
    3: ["out_02_structuring.md", "case01.md"],
    4: ["out_03_history.md", "out_02_structuring.md"],
    5: ["out_04_copy.md", "out_02_structuring.md"],
    6: ["out_04_copy.md", "out_02_structuring.md"],
    7: ["out_04_copy.md", "out_05_geo.md", "out_06_sensitivity.md", "out_02_structuring.md"],
}

HINTS: dict[str, str] = {
    "out_02_structuring.md": "python scripts/gemini/call.py --system docs/agents/prompts/system_02_structuring.txt --user scripts/gemini/private/case01.md > scripts/gemini/private/out_02_structuring.md",
    "out_03_history.md": "python scripts/gemini/compose_agent_user.py --round 3 -o scripts/gemini/private/user_03.txt && python scripts/gemini/call.py --system docs/agents/prompts/system_03_history_sources.txt --user scripts/gemini/private/user_03.txt > scripts/gemini/private/out_03_history.md",
    "out_04_copy.md": "python scripts/gemini/compose_agent_user.py --round 4 -o scripts/gemini/private/user_04.txt && python scripts/gemini/call.py --system docs/agents/prompts/system_04_copy_editor.txt --user scripts/gemini/private/user_04.txt > scripts/gemini/private/out_04_copy.md",
    "out_05_geo.md": "python scripts/gemini/compose_agent_user.py --round 5 -o scripts/gemini/private/user_05.txt && python scripts/gemini/call.py --system docs/agents/prompts/system_05_geo.txt --user scripts/gemini/private/user_05.txt > scripts/gemini/private/out_05_geo.md",
    "out_06_sensitivity.md": "python scripts/gemini/compose_agent_user.py --round 6 -o scripts/gemini/private/user_06.txt && python scripts/gemini/call.py --system docs/agents/prompts/system_06_sensitivity.txt --user scripts/gemini/private/user_06.txt > scripts/gemini/private/out_06_sensitivity.md",
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--expect-round",
        type=int,
        metavar="N",
        help="即將跑 compose --round N（檢查該輪依賴）",
    )
    args = p.parse_args()

    need = list(REQUIRES.get(args.expect_round or 0, []))
    if not need and args.expect_round:
        print(f"未知 round：{args.expect_round}", file=sys.stderr)
        raise SystemExit(2)
    if not need:
        need = sorted({f for fs in REQUIRES.values() for f in fs})

    missing: list[str] = []
    for name in need:
        path = PRIVATE / name
        if not path.is_file():
            missing.append(name)

    for name in sorted(set(need)):
        path = PRIVATE / name
        mark = "✓" if path.is_file() else "✗"
        print(f"{mark} {name}")

    if missing:
        print("\n缺檔，請先補齊。建議指令：", file=sys.stderr)
        for m in missing:
            if m in HINTS:
                print(f"\n# {m}\n{HINTS[m]}", file=sys.stderr)
        raise SystemExit(1)
    print("\n慣用 private 依賴已齊備（此輪）。", file=sys.stderr)


if __name__ == "__main__":
    main()
