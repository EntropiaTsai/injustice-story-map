"""專案根目錄 .env、預設模型名稱。"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

DEFAULT_MODEL = "gemini-2.0-flash"


def model_name() -> str:
    v = (os.environ.get("GEMINI_MODEL") or "").strip()
    return v or DEFAULT_MODEL


def api_key() -> str | None:
    v = os.environ.get("GEMINI_API_KEY")
    return v.strip() if v else None
