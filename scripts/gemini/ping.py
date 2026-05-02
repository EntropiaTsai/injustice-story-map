#!/usr/bin/env python3
"""連線測試：python scripts/gemini/ping.py [自訂提示]"""
from __future__ import annotations

import sys

import google.generativeai as genai

from config import DEFAULT_MODEL, api_key, model_name


def main() -> None:
    key = api_key()
    if not key:
        print(
            "缺少 GEMINI_API_KEY。請在專案根目錄建立 .env（可複製 env.example），"
            "並至 https://aistudio.google.com/apikey 建立金鑰。",
            file=sys.stderr,
        )
        sys.exit(1)

    prompt = " ".join(sys.argv[1:]).strip() or "請用一句繁體中文確認你已連線成功。"
    genai.configure(api_key=key)
    mname = model_name()
    model = genai.GenerativeModel(model_name=mname)
    result = model.generate_content(prompt)
    text = result.text or ""
    print(f"[model={mname}]\n{text}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        err = str(e).lower()
        if "404" in err or "not found" in err:
            mn = model_name()
            print(
                f"Gemini 可能回傳 404：模型「{mn}」不存在或名稱無效。\n"
                f"請在 .env 修改 GEMINI_MODEL，或暫時刪除該行以使用預設「{DEFAULT_MODEL}」。",
                file=sys.stderr,
            )
        elif "429" in err or "resource exhausted" in err:
            print(
                "429：配額或速率已滿。請稍後再試或更換 GEMINI_MODEL。",
                file=sys.stderr,
            )
        else:
            print(e, file=sys.stderr)
        sys.exit(1)
