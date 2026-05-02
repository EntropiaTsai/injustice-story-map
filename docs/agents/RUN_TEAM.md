# 如何啟動 Agent Team（本機）

先完成 Python 依賴與連線測試（見 [`scripts/gemini/README.md`](../../scripts/gemini/README.md)），再選 **自動管線**（固定全跑 §1→§7，或 **PM orchestrator** 依 §1 決定是否略過 §5–§7）或 **手動／瀏覽器**（依 PM 派工微調）。

---

## 方式 0：自動管線（本機一鍵）

準備**一個純文字素材檔**（表單 JSON、官方摘錄、長段敘事皆可），然後：

```bash
python scripts/gemini/pipeline.py --input path/to/your_material.txt
# 或：§1 產出末尾須含 orchestrator JSON（見 system_01_pm.txt），可略過 §5–§7
python scripts/gemini/pipeline_orchestrated.py --input path/to/your_material.txt
```

每階段結果會寫入 `scripts/gemini/pipeline/runs/run-<時間戳>/`；終端機結束時會印出路徑。選項與限制見 [`scripts/gemini/pipeline/README.md`](../../scripts/gemini/pipeline/README.md)（`pipeline.py` 固定跑滿七階；`pipeline_orchestrated.py` 僅依 PM 略過 §5–§7，不支援改順序）。

若素材是 **`data/reference/twtjdb/` 的 xlsx**（多欄位代碼表），建議先用 [`twtjdb_structured.py`](../../scripts/gemini/twtjdb_structured.py) 匯出 **`.json` + 主表 `.md`**（結構化專員較好處理），再當 `call.py`／管線的輸入；亦可改用舊版純文字 [`material_from_twtjdb.py`](../../scripts/gemini/material_from_twtjdb.py)。步驟見 [`data/reference/twtjdb/README.md`](../../data/reference/twtjdb/README.md)。

---

## 方式 A：瀏覽器（Gemini 網頁／AI Studio）

1. 打開 [Google AI Studio](https://aistudio.google.com/) 或 Gemini 網頁版。  
2. 從 [`AGENT_TEAM_PROMPTS.md`](./AGENT_TEAM_PROMPTS.md) **複製 §1 PM 的 System prompt**（含「全域約束」）到自訂指令／系統欄位（依介面而定）。  
3. **User 訊息**貼：投稿內容 +（選）既有故事摘要（見下方「沒有 JSON」）。  
4. 存下輸出後，再開新對話跑 §2、§3…，**User** 請貼「上一棒完整輸出 + 本輪需要的脈絡」。  
5. 順序與協作規則見 `AGENT_TEAM_PROMPTS` 開頭的流程與「協作與迭代」。

---

## 方式 B：專案內 Python 呼叫

使用 **`python scripts/gemini/call.py`**，讓 Gemini 讀兩個**純文字檔**：

| 參數 | 內容 |
|------|------|
| `--system` | 該角色的 **System instruction 全文**（可直接用 [`docs/agents/prompts/system_XX_*.txt`](./prompts/)，或從 `AGENT_TEAM_PROMPTS.md` 複製） |
| `--user` | 該輪 **User 訊息**（投稿 JSON **或** 等價文字、上一棒輸出、你的指示等） |

**範例**（請先自建 `scripts/gemini/private/`，此目錄已列入 `.gitignore`）：

```bash
mkdir -p scripts/gemini/private

# user_pm.txt：貼上投稿內容（見 scripts/gemini/examples/；無 JSON 可用 user_pm_direct_data.example.txt）

python scripts/gemini/call.py \
  --system docs/agents/prompts/system_01_pm.txt \
  --user scripts/gemini/private/user_pm.txt
```

將輸出存檔再餵下一棒；下一輪 §2 換成 `system_02_structuring.txt` 與對應的 `user` 檔。

詳見 [`scripts/gemini/README.md`](../../scripts/gemini/README.md)。

---

## 沒有投稿表單 JSON 時

網站表單產生的 JSON 只是**方便機讀**；流程上你只要給 **「一筆資料」的等價文字** 即可。

- **§1 PM**：在 User 裡用自然語言或條列寫清：你已知什麼、資料從哪來、是否需對照既有故事。可複製 [`scripts/gemini/examples/user_pm_direct_data.example.txt`](../../scripts/gemini/examples/user_pm_direct_data.example.txt) 當骨架，把【原始資料】填滿。  
- **§2 資料結構化**：`AGENT_TEAM_PROMPTS` 已寫明輸入可以是「投稿 JSON **或等價文字**」—PM／§2 會把內容收成表格與欄位。  
- 若日後要進 repo／後台，再請 §2 或你手動對齊 `OUTPUT_SCHEMAS`／`contributions/*.json` 欄位即可。

---

## 建議順序（摘要）

1. **PM（§1）** → 派工與審核包大綱  
2. **§2 資料結構化** → 後台主表  
3. **§3 台灣歷史資料學** → 考證與事件整併  
4. **§4／§5／§6** → 依 PM 與「協作與迭代」調度（含是否早找 §6）  
5. **§7 UI 工程師** → 需前面素材齊備再跑  

輸出欄位可對照 [`OUTPUT_SCHEMAS.md`](./OUTPUT_SCHEMAS.md)。

---

## 進階：依 PM 動態派工

自動管線為**固定順序**七階。若 PM 建議並行、跳過某角色或第二輪迭代，請改用 **`call.py`** 手動餵各輪 User，或瀏覽器分次對話。
