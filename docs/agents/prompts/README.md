# 各 Agent 現成 System prompt（純文字）

本目錄檔案由 [`AGENT_TEAM_PROMPTS.md`](../AGENT_TEAM_PROMPTS.md) 匯出，**已內嵌完整【全域約束】**，可直接當 Gemini **System instruction** 使用。

| 檔案 | 角色 |
|------|------|
| `system_01_pm.txt` | §1 專案經理 PM |
| `system_02_structuring.txt` | §2 資料結構化專員 |
| `system_03_history_sources.txt` | §3 台灣歷史資料學專員 |
| `system_04_copy_editor.txt` | §4 文字編輯 |
| `system_05_geo.txt` | §5 地理資訊專員 |
| `system_06_sensitivity.txt` | §6 受難者權益及法務專員 |
| `system_07_ui.txt` | §7 UI 工程師 |

`GLOBAL_CONSTRAINTS.txt` 為共用段落單獨檔（已複製進各 `system_*.txt` 末尾；若主文件更新全域約束，請同步改此檔與各 system 檔）。

## 與主文件的關係

- **單一真相來源**仍以 `AGENT_TEAM_PROMPTS.md` 為準；若兩邊不一致，以主文件為準並請更新本目錄。
- 修改角色邏輯時：先改 `AGENT_TEAM_PROMPTS.md`，再覆寫對應的 `system_XX_*.txt`。

## 本機呼叫範例

```bash
python scripts/gemini/call.py \
  --system docs/agents/prompts/system_02_structuring.txt \
  --user scripts/gemini/private/user_round2.txt
```

亦可複製到 `scripts/gemini/private/`（已 gitignore）再改檔名，避免路徑過長。

## User 訊息放哪

仍由你依輪次建立 `user_*.txt`（素材、上一棒輸出、PM 派工文字）；範本見 [`scripts/gemini/examples/`](../../../scripts/gemini/examples/)。
