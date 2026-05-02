#!/usr/bin/env python3
"""
單次呼叫：python scripts/gemini/call.py --system a.txt --user b.txt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config import model_name
from gemini_client import generate


def main() -> None:
    p = argparse.ArgumentParser(
        description="讀取 system / user 純文字檔，送交 Gemini。",
    )
    p.add_argument("--system", required=True, help="System instruction 檔")
    p.add_argument("--user", required=True, help="User 訊息檔")
    args = p.parse_args()

    sp = Path(args.system).read_text(encoding="utf-8").strip()
    up = Path(args.user).read_text(encoding="utf-8").strip()
    if not sp or not up:
        print("system 或 user 檔為空。", file=sys.stderr)
        sys.exit(1)

    try:
        print(generate(sp, up), end="")
    except Exception as e:
        err = str(e).lower()
        if "404" in err or "not found" in err:
            print(
                f"404：模型「{model_name()}」不存在。請檢查 .env 的 GEMINI_MODEL。",
                file=sys.stderr,
            )
        elif "429" in err or "resource exhausted" in err:
            print("429：配額或速率已滿。", file=sys.stderr)
        else:
            print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
