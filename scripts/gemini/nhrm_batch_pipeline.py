"""
Batch runner：NHRM nhrm_id → material → pipeline → publish

一次跑一批 NHRM 記錄：
  1. material_from_nhrm.py  → 素材文字
  2. pipeline_orchestrated.py → §1-§7
  3. story_publish.py (T13)  → public/data/pipeline_stories.json

用法：
  python nhrm_batch_pipeline.py --ids 3939,9528
  python nhrm_batch_pipeline.py --ids-file nhrm_ids.txt
  python nhrm_batch_pipeline.py --ids 3939 --dry-run

斷點續跑：已發布的 id 自動跳過（讀 pipeline_stories.json）。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from config import REPO_ROOT

SCRIPTS_GEMINI = Path(__file__).resolve().parent
PYTHON = sys.executable

PIPELINE_STORIES = REPO_ROOT / "public" / "data" / "pipeline_stories.json"
RUNS_DIR = SCRIPTS_GEMINI / "pipeline" / "runs"


def load_published_ids() -> set[str]:
    if not PIPELINE_STORIES.exists():
        return set()
    with open(PIPELINE_STORIES, encoding="utf-8") as f:
        stories = json.load(f)
    return {str(s["id"]) for s in stories}


def run_step(cmd: list[str], label: str) -> subprocess.CompletedProcess:
    print(f"  → {label}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [FAILED] {label}", file=sys.stderr)
        print(result.stderr[-1000:], file=sys.stderr)
    else:
        # print stderr (progress) from sub-process
        if result.stderr.strip():
            for line in result.stderr.strip().splitlines()[-5:]:
                print(f"    {line}", file=sys.stderr)
    return result


def process_one(nhrm_id: int, dry_run: bool) -> bool:
    """跑完整條鏈，回傳是否成功。"""
    import tempfile
    from datetime import datetime, timezone

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    run_dir = RUNS_DIR / f"nhrm-{nhrm_id}-{stamp}"

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        material_path = Path(f.name)

    try:
        # Step 1: 生素材
        r = run_step(
            [PYTHON, str(SCRIPTS_GEMINI / "material_from_nhrm.py"),
             "--id", str(nhrm_id), "--out", str(material_path)],
            "material_from_nhrm"
        )
        if r.returncode != 0:
            return False

        if not material_path.exists() or not material_path.read_text(encoding="utf-8").strip():
            print("  [SKIP] 素材為空", file=sys.stderr)
            return False

        # Step 2: 跑 pipeline
        pipeline_cmd = [
            PYTHON, str(SCRIPTS_GEMINI / "pipeline_orchestrated.py"),
            "--input", str(material_path),
            "--out", str(run_dir),
        ]
        if dry_run:
            pipeline_cmd.append("--dry-run") if False else None  # pipeline 不支援 dry-run，直接跑

        r = run_step(pipeline_cmd, "pipeline_orchestrated §1-§7")
        if r.returncode != 0:
            return False

        # Step 3: 發布
        md_path = run_dir / "07_ui.md"
        if not md_path.exists():
            print(f"  [SKIP] 找不到 {md_path}", file=sys.stderr)
            return False

        publish_cmd = [
            PYTHON, str(SCRIPTS_GEMINI / "story_publish.py"),
            "--md", str(md_path),
        ]
        if dry_run:
            publish_cmd.append("--dry-run")

        r = run_step(publish_cmd, "story_publish (T13)")
        return r.returncode == 0

    finally:
        material_path.unlink(missing_ok=True)


def main() -> None:
    p = argparse.ArgumentParser(description="NHRM batch pipeline runner")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--ids", help="逗號分隔的 nhrm_id，如 3939,9528")
    g.add_argument("--ids-file", type=Path, metavar="FILE", help="每行一個 nhrm_id 的文字檔")
    p.add_argument("--delay", type=float, default=5.0, help="每筆之間的等待秒數（預設 5）")
    p.add_argument("--dry-run", action="store_true", help="pipeline 正常跑但不寫入 pipeline_stories.json")
    p.add_argument("--force", action="store_true", help="即使已發布也重新跑")
    args = p.parse_args()

    # 解析 ID 清單
    if args.ids:
        nhrm_ids = [int(x.strip()) for x in args.ids.split(",") if x.strip()]
    else:
        nhrm_ids = [int(line.strip()) for line in args.ids_file.read_text(encoding="utf-8").splitlines()
                    if line.strip() and not line.startswith("#")]

    published = load_published_ids()
    pending = [nid for nid in nhrm_ids if args.force or str(nid) not in published]

    print(f"[batch] 共 {len(nhrm_ids)} 筆，已發布 {len(published)} 筆，待處理 {len(pending)} 筆", file=sys.stderr)
    if not pending:
        print("[batch] 全部已處理，結束。", file=sys.stderr)
        return

    ok = fail = 0
    for i, nid in enumerate(pending, 1):
        print(f"\n[{i}/{len(pending)}] nhrm_id={nid}", file=sys.stderr)
        success = process_one(nid, dry_run=args.dry_run)
        if success:
            ok += 1
        else:
            fail += 1

        if i < len(pending):
            time.sleep(args.delay)

    print(f"\n[batch] 完成：成功 {ok} 筆，失敗 {fail} 筆", file=sys.stderr)


if __name__ == "__main__":
    main()
