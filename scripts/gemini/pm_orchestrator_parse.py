"""自 PM 產出文字解析 orchestrator JSON。"""
from __future__ import annotations

import json
import re
from typing import Any

from pipeline_common import STAGES, STAGES_PM_MUST_RUN

VALID_STAGE_KEYS = frozenset(k for k, _, _ in STAGES if k != "01_pm")


def parse_pm_orchestrator(pm_markdown: str) -> tuple[set[str], dict[str, str]]:
    """
    回傳 (skip_stages, skip_reasons)。
    找不到合法區塊時回傳 (set(), {}) = 不略過任何可選階段。
    """
    blocks = re.findall(r"```json\s*([\s\S]*?)\s*```", pm_markdown, flags=re.IGNORECASE)
    # 採用「最後一個」可解析且含 orchestrator 的區塊（避免文中範例 JSON 誤判）
    for raw in reversed(blocks):
        raw = raw.strip()
        if not raw:
            continue
        try:
            data: Any = json.loads(raw)
        except json.JSONDecodeError:
            continue
        orch = data.get("orchestrator")
        if not isinstance(orch, dict):
            continue
        skips = orch.get("skip_stages")
        if not isinstance(skips, list):
            skips = []
        skip_set: set[str] = set()
        for x in skips:
            if isinstance(x, str) and x in VALID_STAGE_KEYS:
                skip_set.add(x)
        reasons = orch.get("skip_reasons")
        reason_map: dict[str, str] = {}
        if isinstance(reasons, dict):
            for k, v in reasons.items():
                if isinstance(k, str) and isinstance(v, str) and k in skip_set:
                    reason_map[k] = v.strip()
        return skip_set, reason_map
    return set(), {}


def validate_pm_skips(skip_set: set[str]) -> None:
    bad = skip_set & STAGES_PM_MUST_RUN
    if bad:
        raise ValueError(
            "PM 之 orchestrator.skip_stages 不可略過以下階段（下游硬依賴）："
            + ", ".join(sorted(bad))
            + "。可略過者僅限：05_geo、06_sensitivity、07_ui。"
        )
