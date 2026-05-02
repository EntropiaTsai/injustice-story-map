"""共用：單次呼叫 Gemini（system instruction + user）。"""
from __future__ import annotations

import google.generativeai as genai

from config import api_key, model_name


def generate(system_instruction: str, user_text: str) -> str:
    key = api_key()
    if not key:
        raise RuntimeError(
            "缺少 GEMINI_API_KEY。請在專案根目錄建立 .env（見 env.example）。",
        )
    genai.configure(api_key=key)
    model = genai.GenerativeModel(
        model_name=model_name(),
        system_instruction=system_instruction.strip(),
    )
    resp = model.generate_content(user_text.strip())
    t = (resp.text or "").rstrip("\n")
    return t + "\n" if t else ""
