# 範例檔（§1 PM 的 User 訊息）

預設流程是**一律從 PM（§1）開始**：你把素材貼進下面其中一種範本，PM 判讀後再派工。若為**非表單**，PM 會指示**先交資料結構化專員（§2）**——那是**下一輪**呼叫，請另建 `user` 檔並搭配 `docs/agents/prompts/system_02_structuring.txt`。

- **`user_pm.example.txt`**：網站表單風格 **JSON** 投稿時，給 PM 的 User 訊息範本。  
- **`user_pm_direct_data.example.txt`**：沒有表單 JSON、只有**已取得的敘述／筆記／摘錄**時用；把【原始資料】換成你的內容即可（仍貼給 **PM**）。

**System prompt**：請用 [`docs/agents/prompts/system_01_pm.txt`](../../../docs/agents/prompts/system_01_pm.txt)。

§1 範例呼叫：

```bash
python scripts/gemini/call.py \
  --system docs/agents/prompts/system_01_pm.txt \
  --user scripts/gemini/private/user_pm.txt
```

（若習慣把檔案放在 `private/`，路徑依你的實際檔名調整。）
