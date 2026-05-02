#!/usr/bin/env python3
"""
PM orchestrator 管線：先跑 §1，自 PM 全文最後一個 ```json``` 解析 orchestrator，
可略過 §5–§7（§2–§4 不可略過）。

  python scripts/gemini/pipeline_orchestrated.py --input <素材.txt>
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
from pipeline_common import PROMPTS_DIR, STAGES, build_user_for_stage, skip_placeholder
from pm_orchestrator_parse import parse_pm_orchestrator, validate_pm_skips
from twtjdb_row import DEFAULT_XLSX
from twtjdb_run_registry import record_batch_after_pipeline


def main() -> None:
    p = argparse.ArgumentParser(
        description="§1 後依 PM 之 orchestrator JSON 決定是否略過 §5–§7"
    )
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
        help="管線成功後：將逗號分隔的 twtjdb 列 id 寫入登錄",
    )
    p.add_argument(
        "--record-twtjdb-no-resolve-siblings",
        action="store_true",
        help="搭配 --record-twtjdb-find-id：只登錄該單一 id",
    )
    p.add_argument(
        "--twtjdb-registry",
        type=Path,
        default=None,
        help="登錄 JSONL 路徑（預設 scripts/gemini/private/twtjdb_processed_ids.jsonl）",
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

    print(f"[pipeline_orchestrated] 輸出目錄: {out_dir}", file=sys.stderr)
    print(f"[pipeline_orchestrated] 模型: {mn}", file=sys.stderr)
    print("", file=sys.stderr)

    # §1 PM
    key0, fname0, label0 = STAGES[0]
    system0 = (PROMPTS_DIR / fname0).read_text(encoding="utf-8")
    user0 = build_user_for_stage(key0, outputs, material, existing, cid)
    sys.stderr.write(f"[pipeline_orchestrated] 進行中：{label0} … ")
    sys.stderr.flush()
    t0 = time.perf_counter()
    try:
        text0 = generate(system0, user0)
        outputs[key0] = text0
        (out_dir / f"{key0}.md").write_text(text0, encoding="utf-8")
        dt = time.perf_counter() - t0
        print(f"完成（{dt:.1f}s）", file=sys.stderr)
    except Exception as e:
        print("失敗", file=sys.stderr)
        _print_api_hint(e, mn)
        (out_dir / "FAILED.txt").write_text(f"失敗於：{label0}\n{e!s}", encoding="utf-8")
        sys.exit(1)

    skip_set, reason_map = parse_pm_orchestrator(outputs["01_pm"])
    try:
        validate_pm_skips(skip_set)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    if skip_set:
        print(
            f"[pipeline_orchestrated] PM orchestrator 略過：{sorted(skip_set)}",
            file=sys.stderr,
        )

    for key, fname, label in STAGES[1:]:
        if key in skip_set:
            ph = skip_placeholder(key, reason_map.get(key))
            outputs[key] = ph
            (out_dir / f"{key}.md").write_text(ph, encoding="utf-8")
            print(f"[pipeline_orchestrated] 已略過：{label}（占位 .md）", file=sys.stderr)
            continue

        system = (PROMPTS_DIR / fname).read_text(encoding="utf-8")
        user = build_user_for_stage(key, outputs, material, existing, cid)

        sys.stderr.write(f"[pipeline_orchestrated] 進行中：{label} … ")
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
            _print_api_hint(e, mn)
            (out_dir / "FAILED.txt").write_text(f"失敗於：{label}\n{e!s}", encoding="utf-8")
            sys.exit(1)

    manifest = {
        "model": mn,
        "inputPath": str(Path(args.input).resolve()),
        "outDir": str(out_dir.resolve()),
        "finishedAt": datetime.now(timezone.utc).isoformat(),
        "stages": [k for k, _, _ in STAGES],
        "runner": "python_orchestrated",
        "orchestrator": {
            "source": "01_pm",
            "skip_stages": sorted(skip_set),
            "skip_reasons": reason_map,
        },
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
    print("  PM orchestrator 管線已完成。", file=sys.stderr)
    print(f"  {out_dir}", file=sys.stderr)
    print("══════════════════════════════════════════════════════", file=sys.stderr)


def _print_api_hint(e: BaseException, mn: str) -> None:
    err = str(e).lower()
    if "404" in err or "not found" in err:
        print(f"404：模型「{mn}」不存在。請檢查 .env 的 GEMINI_MODEL。", file=sys.stderr)
    elif "429" in err or "resource exhausted" in err:
        print("429：配額或速率已滿。", file=sys.stderr)
    else:
        print(e, file=sys.stderr)


if __name__ == "__main__":
    main()
