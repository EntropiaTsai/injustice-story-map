# 編輯流程 Agent（Gemini）

版控內容：

| 文件 | 說明 |
|------|------|
| [AGENT_TEAM_PROMPTS.md](./AGENT_TEAM_PROMPTS.md) | 各 sub-agent 職責、輸出格式、System prompt |
| [RUN_TEAM.md](./RUN_TEAM.md) | 本機如何多輪跑 PM → §2…（含 `call.py`） |
| [prompts/](./prompts/) | 各角色現成 `system_*.txt`（已含全域約束，可直接餵 `--system`） |

## 本機 Gemini（Python）

1. 根目錄 `.env` 設定 `GEMINI_API_KEY`（見 `env.example`）。  
2. `pip install -r scripts/gemini/requirements.txt`  
3. `python scripts/gemini/ping.py` 測試連線。  
4. 啟動管線或手動流程：[`RUN_TEAM.md`](./RUN_TEAM.md)、[`scripts/gemini/README.md`](../../scripts/gemini/README.md)。

專案其餘文件（`docs/project/`、`docs/guides/`、`docs/research/` 等）若存在於本機，請見本機 `docs/README.md`；該等路徑預設不納入 Git。
