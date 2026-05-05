"""
NHRM 研究 Agent：以 Gemini function calling 批次查詢國家人權記憶庫。

用法（單筆）：
    python nhrm_researcher.py --name "蕭朝金"

用法（批次，從 make_name_list.py 產生的 JSONL）：
    python nhrm_researcher.py --jsonl names.jsonl --out results.jsonl

--out 支援斷點續跑：已處理的 twtjdb_id 會自動跳過。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

_MAX_RETRIES = 3
_RETRY_DELAY = 15  # 秒

from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gemini"))
from config import api_key, model_name

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from nhrm_scraper import search_person_sync, get_person_detail_sync

# ── 工具定義 ──────────────────────────────────────────────────────────────────

_TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="search_nhrm_person",
                description="在國家人權記憶庫以姓名搜尋受難者，回傳候選名單（含人員 ID）",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "name": types.Schema(type="STRING", description="受難者姓名"),
                    },
                    required=["name"],
                ),
            ),
            types.FunctionDeclaration(
                name="get_nhrm_person_detail",
                description="以人員 ID 取得國家人權記憶庫的詳細資料（簡介、籍貫、平復補償等）",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "person_id": types.Schema(type="INTEGER", description="人員 ID"),
                    },
                    required=["person_id"],
                ),
            ),
        ]
    )
]

_SYSTEM = """你是台灣政治受難歷史研究助理。
給定受難者姓名，用工具在國家人權記憶庫查詢，找到最符合的人員並提取資訊。

查詢流程：
1. search_nhrm_person 搜尋姓名
2. 挑姓名完全一致或最接近的候選，用 get_nhrm_person_detail 取詳細資料
3. 以下列 JSON 格式回覆（只回 JSON，不要其他文字）：

{
  "found": true,
  "person_id": 20608,
  "name": "蕭朝金",
  "birth_year": "1908",
  "death_year": "1947",
  "province": "臺灣",
  "city": "彰化",
  "introduction": "...",
  "recoup": ["依促進轉型正義條例...", "依二二八事件..."],
  "url": "https://..."
}

若無結果：{"found": false, "name": "<查詢姓名>"}"""


def _dispatch(name: str, args: dict[str, Any]) -> Any:
    if name == "search_nhrm_person":
        return search_person_sync(args["name"])
    if name == "get_nhrm_person_detail":
        return get_person_detail_sync(int(args["person_id"]))
    return {"error": f"未知工具：{name}"}


def research_person(name: str) -> dict[str, Any]:
    """查詢單一受難者，回傳結構化結果。"""
    client = genai.Client(api_key=api_key())
    config = types.GenerateContentConfig(
        system_instruction=_SYSTEM,
        tools=_TOOLS,
    )

    messages: list[types.Content] = [
        types.Content(role="user", parts=[types.Part(text=f"請查詢：{name}")])
    ]

    for _ in range(6):
        response = client.models.generate_content(
            model=model_name(), config=config, contents=messages
        )
        candidate = response.candidates[0]
        messages.append(types.Content(role="model", parts=candidate.content.parts))

        fc_parts = [p for p in candidate.content.parts if p.function_call]
        if not fc_parts:
            break

        tool_parts = []
        for p in fc_parts:
            fc = p.function_call
            result = _dispatch(fc.name, dict(fc.args))
            tool_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=fc.name,
                        response={"result": json.dumps(result, ensure_ascii=False)},
                    )
                )
            )
        messages.append(types.Content(role="user", parts=tool_parts))

    text = response.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"found": False, "name": name, "raw": text}


def _load_done_ids(out_path: Path) -> set[str]:
    """從已存在的輸出檔讀取已處理的 twtjdb_id，用於斷點續跑。"""
    done: set[str] = set()
    if not out_path.exists():
        return done
    with open(out_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                if "twtjdb_id" in row:
                    done.add(str(row["twtjdb_id"]))
            except json.JSONDecodeError:
                pass
    return done


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NHRM 研究 Agent")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--name", help="查詢單一姓名")
    group.add_argument("--names", help="逗號分隔的多個姓名")
    group.add_argument("--jsonl", help="JSONL 檔路徑，每行含 name（與可選的 twtjdb_id）")
    parser.add_argument("--out", help="輸出 JSONL 路徑（支援斷點續跑）")
    parser.add_argument("--delay", type=float, default=2.0, help="每筆之間的延遲秒數（預設 2）")
    args = parser.parse_args()

    # 準備名單：list of {"name": str, "twtjdb_id": str | None}
    rows: list[dict[str, Any]] = []
    if args.name:
        rows = [{"name": args.name, "twtjdb_id": None}]
    elif args.names:
        rows = [{"name": n.strip(), "twtjdb_id": None} for n in args.names.split(",") if n.strip()]
    elif args.jsonl:
        with open(args.jsonl, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                rows.append({"name": obj["name"], "twtjdb_id": obj.get("twtjdb_id")})

    # 斷點續跑
    out_path = Path(args.out) if args.out else None
    done_ids = _load_done_ids(out_path) if out_path else set()
    if done_ids:
        print(f"[resume] 已跳過 {len(done_ids)} 筆", file=sys.stderr)

    out_file = open(out_path, "a", encoding="utf-8") if out_path else None

    try:
        for i, row in enumerate(rows):
            tid = str(row["twtjdb_id"]) if row["twtjdb_id"] else None
            if tid and tid in done_ids:
                continue

            print(f"[{i+1}/{len(rows)}] 查詢：{row['name']}", file=sys.stderr)
            result = None
            for attempt in range(1, _MAX_RETRIES + 1):
                try:
                    result = research_person(row["name"])
                    break
                except Exception as e:
                    if attempt < _MAX_RETRIES:
                        print(f"  [retry {attempt}/{_MAX_RETRIES}] {e}，{_RETRY_DELAY}s 後重試", file=sys.stderr)
                        time.sleep(_RETRY_DELAY)
                    else:
                        print(f"  [error] 查詢失敗：{e}", file=sys.stderr)
                        result = {"found": False, "name": row["name"], "error": str(e)}
            if result is None:
                result = {"found": False, "name": row["name"], "error": "unknown"}

            if tid:
                result["twtjdb_id"] = tid

            line = json.dumps(result, ensure_ascii=False)
            print(line)
            sys.stdout.flush()
            if out_file:
                out_file.write(line + "\n")
                out_file.flush()

            if i < len(rows) - 1:
                time.sleep(args.delay)
    finally:
        if out_file:
            out_file.close()
