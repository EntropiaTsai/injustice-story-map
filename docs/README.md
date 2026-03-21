# 專案文件索引

`docs/` 依用途分成幾個子資料夾，方便對照：**專案與技術**、**內容與操作指南**、**編輯自動化（Agent）**、**研究參考資料**。

```
docs/
├── README.md                 ← 本索引
├── project/                  # 計畫、架構、技術、招募
├── guides/                   # 給內容／貢獻者的操作手冊
├── agents/                   # Gemini／投稿處理流程的 prompt 與角色定義
└── research/                 # 名單、驗證指南、個案研究（非「網站說明」）
```

---

## `project/` — 專案與技術

| 文件 | 說明 |
|------|------|
| [PROJECT_PLAN.md](project/PROJECT_PLAN.md) | 專案願景、分工、時程等 |
| [PROJECT_STRUCTURE.md](project/PROJECT_STRUCTURE.md) | 程式與目錄結構說明 |
| [TECHNICAL_SPECS.md](project/TECHNICAL_SPECS.md) | 技術棧、資料結構、部署 |
| [RECRUITMENT.md](project/RECRUITMENT.md) | 招募說明 |

---

## `guides/` — 內容與貢獻指南

| 文件 | 說明 |
|------|------|
| [STORY_COLLECTION_GUIDE.md](guides/STORY_COLLECTION_GUIDE.md) | 故事蒐集原則、格式、提交流程 |
| [HOW_TO_ADD_YOUTUBE_VIDEOS.md](guides/HOW_TO_ADD_YOUTUBE_VIDEOS.md) | 在故事資料中加入 YouTube 影片 |

---

## `agents/` — 編輯流程自動化（Sub-agents / Gemini）

與「故事正文／歷史研究」分開存放，避免和讀者面向的指南混在一起。

| 文件 | 說明 |
|------|------|
| [AGENT_TEAM_PROMPTS.md](agents/AGENT_TEAM_PROMPTS.md) | 各 sub-agent 職責、輸出格式、Gemini System prompt |

---

## `research/` — 研究參考

內部查核、名單與個案筆記；**不作為**對外官網文案的唯一依據，引用時仍須回到原始出處。

- 根目錄：法務部相關名單、受難者查詢與驗證指南等  
- [stories_research/](research/stories_research/)：個案／主題研究筆記  

---

## 備註：版本庫與 `.gitignore`

若根目錄 `.gitignore` 中有規則會忽略整個 `docs/`，這些文件可能不會被 Git 追蹤。若你希望**把文件一併提交到遠端**，請調整忽略規則（例如改為只忽略 `docs/research/` 下的敏感檔案），依你的需求而定。

---

**最後更新**：2026-03-21（目錄重整）
