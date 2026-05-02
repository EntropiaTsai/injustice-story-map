"""管線共用：階段定義、User 訊息組裝（pipeline / pipeline_orchestrated）。"""
from __future__ import annotations

from pathlib import Path

from config import REPO_ROOT

PROMPTS_DIR = REPO_ROOT / "docs" / "agents" / "prompts"

STAGES: list[tuple[str, str, str]] = [
    ("01_pm", "system_01_pm.txt", "§1 PM"),
    ("02_structuring", "system_02_structuring.txt", "§2 資料結構化"),
    ("03_history_sources", "system_03_history_sources.txt", "§3 台灣歷史資料學"),
    ("04_copy_editor", "system_04_copy_editor.txt", "§4 文字編輯"),
    ("05_geo", "system_05_geo.txt", "§5 地理"),
    ("06_sensitivity", "system_06_sensitivity.txt", "§6 權益／敏感度"),
    ("07_ui", "system_07_ui.txt", "§7 UI"),
]

# PM orchestrator 不得略過（下游硬依賴）
STAGES_PM_MUST_RUN = frozenset(
    {"02_structuring", "03_history_sources", "04_copy_editor"}
)


def build_user_pm(material: str, existing_stories: str) -> str:
    es = existing_stories.strip() or "無"
    return f"""請依「專案經理 PM」角色處理以下素材。

【既有故事摘要】
{es}

【原始素材】
{material.strip()}
"""


def build_user_structuring(pm_out: str, material: str) -> str:
    return f"""請依 System 中的「資料結構化專員」角色處出完整輸出。

## PM（§1）產出
{pm_out}

## 原始素材（對照用）
{material.strip()}
"""


def build_user_history(s2: str, material: str) -> str:
    return f"""請依 System 中的「台灣歷史資料學專員」角色產出完整輸出。

## 結構化專員（§2）產出
{s2}

## 原始素材（連結與補充對照用）
{material.strip()}
"""


def build_user_copy(s3: str, s2: str) -> str:
    return f"""請依 System 中的「文字編輯」角色產出完整輸出。

## 台灣歷史資料學專員（§3）產出
{s3}

## 結構化專員（§2）產出（欄位對照）
{s2}
"""


def build_user_geo(s2: str, s4: str) -> str:
    return f"""請依 System 中的「地理資訊專員」角色產出完整輸出。

## 結構化專員（§2）產出
{s2}

## 文字編輯（§4）產出
{s4}
"""


def build_user_sensitivity(s2: str, s4: str) -> str:
    return f"""請依 System 中的「受難者權益及法務專員」角色產出完整輸出。

## 結構化專員（§2）產出
{s2}

## 文字編輯（§4）產出
{s4}
"""


def build_user_ui(
    s2: str, s4: str, s5: str, s6: str, contribution_id: str
) -> str:
    cid = contribution_id or "（未指定 --id，請於 JSON 內用 placeholder）"
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
{cid}
"""


def build_user_for_stage(
    key: str,
    outputs: dict[str, str],
    material: str,
    existing: str,
    contribution_id: str,
) -> str:
    if key == "01_pm":
        return build_user_pm(material, existing)
    if key == "02_structuring":
        return build_user_structuring(outputs["01_pm"], material)
    if key == "03_history_sources":
        return build_user_history(outputs["02_structuring"], material)
    if key == "04_copy_editor":
        return build_user_copy(outputs["03_history_sources"], outputs["02_structuring"])
    if key == "05_geo":
        return build_user_geo(outputs["02_structuring"], outputs["04_copy_editor"])
    if key == "06_sensitivity":
        return build_user_sensitivity(outputs["02_structuring"], outputs["04_copy_editor"])
    if key == "07_ui":
        return build_user_ui(
            outputs["02_structuring"],
            outputs["04_copy_editor"],
            outputs["05_geo"],
            outputs["06_sensitivity"],
            contribution_id,
        )
    raise KeyError(key)


def skip_placeholder(stage_key: str, reason: str | None) -> str:
    r = (reason or "").strip()
    extra = f"\n\n**PM 說明**：{r}" if r else ""
    return (
        f"## 本階段已略過\n\n"
        f"階段代碼：`{stage_key}`。此檔為 **orchestrator** 依 PM 產出之 `orchestrator.skip_stages` 自動建立，"
        f"未呼叫該角色模型。§7 或人工流程請視需要補跑本階。{extra}\n"
    )
