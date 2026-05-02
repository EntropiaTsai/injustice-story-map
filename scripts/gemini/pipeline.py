#!/usr/bin/env python3
"""
自動管線：依序 §1→§7，讀取單一素材檔。

  python scripts/gemini/pipeline.py --input <素材.txt>
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from config import REPO_ROOT, model_name
from gemini_client import generate
from pipeline_common import PROMPTS_DIR, STAGES, build_user_for_stage
from twtjdb_row import DEFAULT_XLSX
from twtjdb_run_registry import record_batch_after_pipeline


def main() -> None:
    p = argparse.ArgumentParser(description="依序跑 §1→§7，結果寫入 pipeline/runs/")
    p.add_argument("--input", required=True, help="素材純文字檔")
    p.add_argument("--out", help="輸出目錄（預設 runs/run-<時間戳>）")
    p.add_argument("--existing-stories", help="既有故事摘要檔")
    p.add_argument("--id", dest="contribution_id", help="投稿 id（§7）")
    p.add_argument(
        "--record-twtjdb-find-id",
        metavar="ID",
        default=None,
        help="管線成功後：依 xlsx 解析同人多案，將相關 twtjdb 列 id 寫入登錄",
    )
    p.add_argument(
        "--record-twtjdb-ids",
        metavar="CSV",
        default=None,
        help="管線成功後：將逗號分隔的 twtjdb 列 id 寫入登錄（不掃描合併）",
    )
    p.add_argument(
        "--record-twtjdb-no-resolve-siblings",
        action="store_true",
        help="搭配 --record-twtjdb-find-id：只登錄該單一 id，不掃描同人列",
    )
    p.add_argument(
        "--twtjdb-registry",
        type=Path,
        default=None,
        help="登錄 JSONL 路徑（預設見 twtjdb_run_registry.py）",
    )
    args = p.parse_args()

    material = Path(args.input).read_text(encoding="utf-8")
    if not material.strip():
        print("素材檔為空。", file=sys.stderr)
        sys.exit(1)

    existing = "無"
    if args.existing_stories:
        existing = Path(args.existing_stories).read_text(encoding="utf-8")

    stamp = datetime.now(timezone.utc).isoformat().replace(":", "-").replace(".", "-")
    if args.out:
        out_dir = Path(args.out)
    else:
        out_dir = REPO_ROOT / "scripts" / "gemini" / "pipeline" / "runs" / f"run-{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    outputs: dict[str, str] = {}
    mn = model_name()
    cid = args.contribution_id or ""

    print(f"[pipeline] 輸出目錄: {out_dir}", file=sys.stderr)
    print(f"[pipeline] 模型: {mn}", file=sys.stderr)
    print("", file=sys.stderr)

    for key, fname, label in STAGES:
        system = (PROMPTS_DIR / fname).read_text(encoding="utf-8")
        user = build_user_for_stage(key, outputs, material, existing, cid)

        sys.stderr.write(f"[pipeline] 進行中：{label} … ")
        sys.stderr.flush()
        t0 = time.perf_counter()
        try:
            text = generate(system, user)
            outputs[key] = text
            (out_dir / f"{key}.md").write_text(text, encoding="utf-8")
            dt = time.perf_counter() - t0
            print(f"完成（{dt:.1f}s）", file=sys.stderr)
        except Exception as e:
            print("失敗", file=sys.stderr)
            err = str(e).lower()
            if "404" in err or "not found" in err:
                print(f"404：模型「{mn}」不存在。請檢查 .env 的 GEMINI_MODEL。", file=sys.stderr)
            elif "429" in err or "resource exhausted" in err:
                print("429：配額或速率已滿。", file=sys.stderr)
            else:
                print(e, file=sys.stderr)
            (out_dir / "FAILED.txt").write_text(f"失敗於：{label}\n{e!s}", encoding="utf-8")
            sys.exit(1)

    manifest = {
        "model": mn,
        "inputPath": str(Path(args.input).resolve()),
        "outDir": str(out_dir.resolve()),
        "finishedAt": datetime.now(timezone.utc).isoformat(),
        "stages": [k for k, _, _ in STAGES],
        "runner": "python",
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    record_batch_after_pipeline(
        registry=args.twtjdb_registry,
        find_id=args.record_twtjdb_find_id,
        ids_csv=args.record_twtjdb_ids,
        no_resolve_siblings=args.record_twtjdb_no_resolve_siblings,
        xlsx=DEFAULT_XLSX,
        run_dir=out_dir,
        note="",
    )

    print("", file=sys.stderr)
    print("══════════════════════════════════════════════════════", file=sys.stderr)
    print("  管線已完成。每階段結果已寫入上述目錄中的 .md 檔。", file=sys.stderr)
    print(f"  {out_dir}", file=sys.stderr)
    print("══════════════════════════════════════════════════════", file=sys.stderr)


if __name__ == "__main__":
    main()
