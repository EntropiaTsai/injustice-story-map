"""
T22 — nhrm_archive_agent：本地 NHRM 資料查詢 agent（Gemini function calling）

從 data/processed/nhrm_merged.json 查詢受難者資料，不需打 live 網站。
供 §3（台灣歷史資料學）、PM 或人工互動使用。

用法（互動問答）：
  python nhrm_archive_agent.py

用法（單一問題）：
  python nhrm_archive_agent.py --ask "台南市工委會大內支部有哪些人？"
  python nhrm_archive_agent.py --ask "童常的完整傳記"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gemini"))
from config import REPO_ROOT, api_key, model_name

NHRM_MERGED = REPO_ROOT / "data" / "processed" / "nhrm_merged.json"

# ── 資料載入（模組層級，只載一次）────────────────────────────────────────────

_persons_by_id: dict[int, dict] = {}
_persons_list: list[dict] = []


def _ensure_loaded() -> None:
    if _persons_by_id:
        return
    with open(NHRM_MERGED, encoding="utf-8") as f:
        data = json.load(f)
    for p in data["persons"]:
        _persons_by_id[p["nhrm_id"]] = p
        _persons_list.append(p)
    print(f"[nhrm_archive] 已載入 {len(_persons_list)} 筆", file=sys.stderr)


# ── 工具實作 ──────────────────────────────────────────────────────────────────

def _fmt_person_summary(p: dict) -> dict:
    """回傳精簡摘要（供搜尋結果列表用）。"""
    j = p.get("judgment") or {}
    return {
        "nhrm_id": p["nhrm_id"],
        "twtjdb_id": p.get("twtjdb_id"),
        "name": p.get("name"),
        "nickname": p.get("nickname"),
        "gender": p.get("gender"),
        "birth_year": p.get("birth_year"),
        "death_year": p.get("death_year"),
        "province": p.get("province"),
        "city": p.get("city"),
        "penalty_level": p.get("penalty_level"),
        "penalty_text": j.get("penalty_text"),
        "has_death_penalty": j.get("has_death_penalty", False),
        "nhrm_url": p.get("nhrm_url"),
        "intro_excerpt": (p.get("introduction") or "")[:150],
    }


def _fmt_person_full(p: dict) -> dict:
    """回傳完整資料（含 introduction、cases、related_persons 等）。"""
    j = p.get("judgment") or {}
    org = j.get("organization") or ""
    org = org.replace("歷年辦理匪案彙編：", "").replace("歷年辦理匪案彙編:", "")
    if org.startswith("匪"):
        org = org[1:]

    seen: set[int] = set()
    unique_related = []
    for r in (p.get("related_persons") or []):
        if r["nhrm_id"] not in seen:
            seen.add(r["nhrm_id"])
            unique_related.append(r)

    return {
        "nhrm_id": p["nhrm_id"],
        "twtjdb_id": p.get("twtjdb_id"),
        "name": p.get("name"),
        "nickname": p.get("nickname"),
        "gender": p.get("gender"),
        "birth_year": p.get("birth_year"),
        "death_year": p.get("death_year"),
        "province": p.get("province"),
        "city": p.get("city"),
        "place": p.get("place"),
        "penalty_level": p.get("penalty_level"),
        "judgment": {
            "authority": j.get("authority"),
            "year_roc": j.get("year_roc"),
            "penalty_text": j.get("penalty_text"),
            "has_death_penalty": j.get("has_death_penalty", False),
            "has_life_sentence": j.get("has_life_sentence", False),
            "organization": org or None,
        },
        "nhrm_penalty": p.get("nhrm_penalty") or [],
        "introduction": p.get("introduction"),
        "cases": p.get("cases") or [],
        "related_persons": unique_related,
        "recoup": p.get("recoup") or [],
        "documents": [
            {"title": d.get("title"), "authority": d.get("authority"), "date": d.get("date")}
            for d in (p.get("documents") or [])
        ],
        "nhrm_url": p.get("nhrm_url"),
        "image_url": p.get("image_url"),
    }


def tool_search_by_name(name: str, exact: bool = False) -> list[dict]:
    """依姓名搜尋（模糊或完全符合），回傳摘要清單。"""
    _ensure_loaded()
    results = []
    for p in _persons_list:
        pname = p.get("name") or ""
        nick = p.get("nickname") or ""
        if exact:
            if name == pname or name == nick:
                results.append(_fmt_person_summary(p))
        else:
            if name in pname or name in nick or (nick and nick in name):
                results.append(_fmt_person_summary(p))
    return results[:50]  # 最多回 50 筆


def tool_get_person(nhrm_id: int) -> dict:
    """依 nhrm_id 取得完整受難者資料。"""
    _ensure_loaded()
    p = _persons_by_id.get(nhrm_id)
    if p is None:
        return {"error": f"nhrm_id {nhrm_id} 不存在"}
    return _fmt_person_full(p)


def tool_search_by_case(case_name: str) -> list[dict]:
    """搜尋參與特定案件的所有受難者（比對 cases[].name 與 introduction）。"""
    _ensure_loaded()
    results = []
    for p in _persons_list:
        # 比對 cases 欄位
        for c in (p.get("cases") or []):
            if case_name in (c.get("name") or ""):
                results.append(_fmt_person_summary(p))
                break
        else:
            # fallback：比對 introduction
            if case_name in (p.get("introduction") or ""):
                results.append(_fmt_person_summary(p))
    return results[:100]


def tool_get_related_persons(nhrm_id: int) -> list[dict]:
    """取得某人的同案相關人物（已去重），並附上各人摘要。"""
    _ensure_loaded()
    p = _persons_by_id.get(nhrm_id)
    if p is None:
        return [{"error": f"nhrm_id {nhrm_id} 不存在"}]
    seen: set[int] = set()
    results = []
    for r in (p.get("related_persons") or []):
        if r["nhrm_id"] in seen:
            continue
        seen.add(r["nhrm_id"])
        related_p = _persons_by_id.get(r["nhrm_id"])
        if related_p:
            results.append(_fmt_person_summary(related_p))
        else:
            results.append({"nhrm_id": r["nhrm_id"], "name": r["name"]})
    return results


# ── Gemini Function Declarations ──────────────────────────────────────────────

_TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="search_by_name",
                description="依姓名搜尋受難者，回傳摘要清單（含 nhrm_id、生卒、刑罰、傳記摘要）",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "name": types.Schema(type="STRING", description="姓名或部分姓名"),
                        "exact": types.Schema(type="BOOLEAN", description="true=完全符合，false=模糊（預設）"),
                    },
                    required=["name"],
                ),
            ),
            types.FunctionDeclaration(
                name="get_person",
                description="依 nhrm_id 取得完整受難者資料（傳記、判決、相關人物、文件等）",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "nhrm_id": types.Schema(type="INTEGER", description="NHRM 人員 ID"),
                    },
                    required=["nhrm_id"],
                ),
            ),
            types.FunctionDeclaration(
                name="search_by_case",
                description="搜尋參與特定案件的所有受難者（比對案件名稱或傳記文字）",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "case_name": types.Schema(type="STRING", description="案件名稱關鍵字，如「鹿窟事件」「大內支部」"),
                    },
                    required=["case_name"],
                ),
            ),
            types.FunctionDeclaration(
                name="get_related_persons",
                description="取得某受難者的同案相關人物清單（已去重）",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "nhrm_id": types.Schema(type="INTEGER", description="NHRM 人員 ID"),
                    },
                    required=["nhrm_id"],
                ),
            ),
        ]
    )
]

_SYSTEM = """\
你是「國家人權記憶庫本地查詢助理」，專門協助研究台灣白色恐怖時期受難者資料。
你有完整的 12,060 筆 NHRM 受難者資料可以查詢（本地資料庫，無需連網）。

可用工具：
- search_by_name：依姓名搜尋
- get_person：依 nhrm_id 取完整資料（含傳記、判決、相關人物）
- search_by_case：依案件名稱搜尋所有涉案受難者
- get_related_persons：取得某人的同案人物

回答時盡量引用資料中的具體細節（年份、案號、組織名稱）。
若資料庫中找不到，如實說明，不要捏造。"""


def _dispatch(name: str, args: dict[str, Any]) -> Any:
    if name == "search_by_name":
        return tool_search_by_name(args["name"], args.get("exact", False))
    if name == "get_person":
        return tool_get_person(int(args["nhrm_id"]))
    if name == "search_by_case":
        return tool_search_by_case(args["case_name"])
    if name == "get_related_persons":
        return tool_get_related_persons(int(args["nhrm_id"]))
    return {"error": f"未知工具：{name}"}


def ask(question: str, client: genai.Client) -> str:
    config = types.GenerateContentConfig(
        system_instruction=_SYSTEM,
        tools=_TOOLS,
        temperature=0.1,
    )
    messages: list[types.Content] = [
        types.Content(role="user", parts=[types.Part(text=question)])
    ]

    for _ in range(8):
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

    return response.text or ""


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NHRM 本地資料庫查詢 agent（T22）")
    parser.add_argument("--ask", help="單一問題（不給則進入互動模式）")
    args = parser.parse_args()

    client = genai.Client(api_key=api_key())
    _ensure_loaded()

    if args.ask:
        print(ask(args.ask, client))
    else:
        print("NHRM 本地查詢 Agent（輸入 q 離開）", file=sys.stderr)
        while True:
            try:
                q = input("\n問題：").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if q.lower() in ("q", "quit", "exit", ""):
                break
            print(ask(q, client))
