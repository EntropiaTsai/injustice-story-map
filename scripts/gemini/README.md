# Gemini 本機腳本（Python）

非前端、與編輯管線相關的程式**以 Python 為準**（`src/` 內 React／TS 僅服務頁面）。

需專案根目錄 `.env`：`GEMINI_API_KEY`、選用 `GEMINI_MODEL`（見 `env.example`）。金鑰勿寫進前端。

## 安裝（一次性）

於專案根目錄：

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r scripts/gemini/requirements.txt
```

## 指令

| 用途 | 指令 |
|------|------|
| 連線測試 | `python scripts/gemini/ping.py` |
| 自訂一句 | `python scripts/gemini/ping.py 你好` |
| 單次呼叫（某角色） | `python scripts/gemini/call.py --system docs/agents/prompts/system_01_pm.txt --user scripts/gemini/private/user_pm.txt` |
| 自動管線 §1→§7（固定全跑） | `python scripts/gemini/pipeline.py --input scripts/gemini/private/material.txt` |
| 自動管線（§1 決定是否略過 §5–§7） | `python scripts/gemini/pipeline_orchestrated.py --input scripts/gemini/private/material.txt` |
| 從 twtjdb xlsx **結構化**匯出（JSON + 主表 .md，推薦給 §2） | `python scripts/gemini/twtjdb_structured.py --row 2 --out-base scripts/gemini/private/case01` |
| twtjdb **全表**每筆各一組 json+md | `python scripts/gemini/twtjdb_export_all.py --out-dir scripts/gemini/private/twtjdb_all`（可加 `--limit 20` 試跑、`--skip-existing` 續跑） |
| 從 twtjdb 匯出純文字單列 | `python scripts/gemini/material_from_twtjdb.py --row 2 --out scripts/gemini/private/twtjdb.txt` |
| 同人多案合併（預設） | `--find-id`／`--row` 時會掃描全 xlsx，姓名核心＋出生年＋籍貫相同則合併多段輸出；僅單列加 `--no-merge-siblings`（`material_from_twtjdb` 與 `twtjdb_structured` 皆支援） |
| 已跑管線 id 登錄（本機） | `python scripts/gemini/twtjdb_run_registry.py check --find-id 11947`（exit 0＝尚未登錄、2＝整批已跑過）；跑完管線可加 `--record-twtjdb-find-id 11947` 自動寫入 `private/twtjdb_processed_ids.jsonl`（見同目錄 `twtjdb_processed_ids.example.jsonl`） |

### 素材在 `data/reference/twtjdb/`（xlsx）

**建議**：用 **`twtjdb_structured.py`** 產生 `*.json`（機讀分組）與 `*.md`（主表草稿），再餵 **§2** 或整條管線：

```bash
python scripts/gemini/twtjdb_structured.py --row 2 --out-base scripts/gemini/private/case01
python scripts/gemini/call.py --system docs/agents/prompts/system_02_structuring.txt --user scripts/gemini/private/case01.md
# 或：python scripts/gemini/pipeline.py --input scripts/gemini/private/case01.md
```

純文字版（較不結構化）：`material_from_twtjdb.py` → `pipeline.py`。  
說明：[`data/reference/twtjdb/README.md`](../../data/reference/twtjdb/README.md)、工具登錄 **T02b**：[`docs/agents/TOOLS.md`](../../docs/agents/TOOLS.md)。

## 路徑說明

| 路徑 | 內容 |
|------|------|
| `docs/agents/prompts/system_*.txt` | 各角色 System prompt（版控） |
| `examples/` | §1 User 訊息範本 |
| `pipeline/runs/` | 管線輸出（預設 gitignore） |
| `private/` | 本機素材／user 檔（gitignore） |

## 模型名稱

預設 `gemini-2.0-flash`，可於 `.env` 設 `GEMINI_MODEL`。**404** 多為無效 model id；**429** 為配額／速率，見 [官方說明](https://ai.google.dev/gemini-api/docs/rate-limits)。

## 手動多輪：組下一棒 User 檔

跑 `compose_agent_user.py --round 4` 前，**必須已有** `out_03_history.md`（先跑 §3）。可先檢查：

```bash
python scripts/gemini/check_private_inputs.py --expect-round 4
```

不必手建 `user_03.txt`：若 §2、素材檔已放在 `private/` 慣用檔名，可：

```bash
python scripts/gemini/compose_agent_user.py --round 3 -o scripts/gemini/private/user_03.txt
python scripts/gemini/call.py --system docs/agents/prompts/system_03_history_sources.txt \
  --user scripts/gemini/private/user_03.txt > scripts/gemini/private/out_03_history.md
```

`--round` 可為 3–7；預設讀 `out_02_structuring.md`、`case01.md` 等（見腳本 `--help`）。

## 延伸閱讀

- [`pipeline/README.md`](pipeline/README.md) — 管線選項與限制  
- [`docs/agents/RUN_TEAM.md`](../../docs/agents/RUN_TEAM.md) — 手動多輪或瀏覽器流程  
