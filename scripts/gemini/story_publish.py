"""
T13 — story_publish：從 pipeline run 的 07_ui.md 解析 JSON，
寫入 public/data/pipeline_stories.json（追加或更新）。

用法：
  python story_publish.py --run scripts/gemini/pipeline/runs/run-2026-03-29.../
  python story_publish.py --md scripts/gemini/pipeline/runs/.../07_ui.md
  python story_publish.py --run ... --dry-run   # 只印結果不寫入
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from config import REPO_ROOT

OUT_JSON = REPO_ROOT / "public" / "data" / "pipeline_stories.json"


def extract_json_from_md(md_path: Path) -> dict:
    """從 07_ui.md 的第一個 ```json 區塊取出 JSON。"""
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"```json\s*\n([\s\S]*?)\n```", text)
    if not m:
        raise ValueError(f"找不到 ```json 區塊：{md_path}")
    return json.loads(m.group(1))


def normalize(story: dict) -> dict:
    """統一欄位型別，讓格式和 StoryLocation 一致。"""
    # year → 字串
    if isinstance(story.get("year"), int):
        story["year"] = str(story["year"])
    # lat/lng null → 移除（無座標就不上地圖，不報錯）
    if story.get("lat") is None:
        story.pop("lat", None)
        story.pop("lng", None)
    # 確保必要陣列存在
    for key in ("images", "youtubeVideos", "relatedLinks", "tags"):
        if key not in story:
            story[key] = []
    # source 標記
    story["source"] = "pipeline"
    # 移除空的 relatedLinks（url = 待補網址）
    story["relatedLinks"] = [
        r for r in story.get("relatedLinks", [])
        if r.get("url") and r["url"] not in ("待補網址", "", None)
    ]
    return story



def publish(story: dict, dry_run: bool = False, out: Path = OUT_JSON) -> str:
    """新增或更新一筆故事，回傳狀態說明。"""
    story = normalize(story)
    sid = story.get("id")
    if not sid:
        raise ValueError("story 缺少 id 欄位")

    if out.exists():
        with open(out, encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = []

    ids = [s["id"] for s in existing]
    if sid in ids:
        existing[ids.index(sid)] = story
        action = f"更新 (id={sid})"
    else:
        existing.append(story)
        action = f"新增 (id={sid})"

    if not dry_run:
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"[story_publish] {action} → {out}（共 {len(existing)} 筆）", file=sys.stderr)
    else:
        print(f"[story_publish] dry-run {action}", file=sys.stderr)
        print(json.dumps(story, ensure_ascii=False, indent=2))

    return action


def main() -> None:
    p = argparse.ArgumentParser(description="T13：pipeline run → pipeline_stories.json")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", type=Path, metavar="DIR", help="pipeline run 目錄（含 07_ui.md）")
    g.add_argument("--md", type=Path, metavar="FILE", help="07_ui.md 路徑")
    p.add_argument("--dry-run", action="store_true", help="只印結果，不寫入檔案")
    p.add_argument("--out", type=Path, default=OUT_JSON, help="輸出 JSON 路徑")
    args = p.parse_args()

    md_path = (args.run / "07_ui.md") if args.run else args.md
    if not md_path.exists():
        print(f"找不到：{md_path}", file=sys.stderr)
        sys.exit(1)

    story = extract_json_from_md(md_path)
    publish(story, dry_run=args.dry_run, out=args.out.resolve())


if __name__ == "__main__":
    main()
