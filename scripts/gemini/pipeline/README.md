# 自動管線

讀取**單一素材檔**，每階段結果寫入 `runs/run-<時間戳>/`。

## 兩種跑法

| 腳本 | 行為 |
|------|------|
| `pipeline.py` | 固定依序 **§1 → §7** 全跑 |
| `pipeline_orchestrated.py` | 先跑 **§1 PM**，自 PM 全文**最後一個**語言為 `json` 的 fenced 區塊讀取 `orchestrator.skip_stages`，可略過 **§5、§6、§7**；§2–§4 不可略過。略過的階段仍會寫入占位 `.md`，供 §7 或人工補跑。`manifest.json` 會記錄 `orchestrator`。 |

PM 輸出格式見 `docs/agents/prompts/system_01_pm.txt`（文末 JSON）。

## 使用

```bash
# 先安裝依賴（見上層 README）
pip install -r scripts/gemini/requirements.txt

cp scripts/gemini/pipeline/input.example.txt scripts/gemini/private/my_material.txt
# 編輯 my_material.txt

python scripts/gemini/pipeline.py --input scripts/gemini/private/my_material.txt
# 或：python scripts/gemini/pipeline_orchestrated.py --input scripts/gemini/private/my_material.txt
```

完成時終端機會印出**輸出目錄**；內含 `01_pm.md` … `07_ui.md`、`manifest.json`。

### 選用參數

| 參數 | 說明 |
|------|------|
| `--out <目錄>` | 指定輸出目錄 |
| `--existing-stories <檔>` | 既有故事摘要（純文字），供 §1 |
| `--id <字串>` | 供 §7 參考的投稿 id |

## 限制

- **`pipeline.py`**：固定順序七階，不解析 PM。
- **`pipeline_orchestrated.py`**：僅支援在預設鏈上**略過 §5–§7**，不支援改順序或並行；更細控制請用 `call.py` 手動。
- **上下文長度**：後段會帶入前段全文；素材極長時可能觸及模型上限。
- **配額**：七輪 API；遇 **429** 會中止並寫入 `FAILED.txt`。

## 與手動流程

見 [`docs/agents/RUN_TEAM.md`](../../../docs/agents/RUN_TEAM.md)。
