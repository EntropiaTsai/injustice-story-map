# 台灣不義遺址故事地圖

> 透過互動式地圖，探索你家鄉的歷史記憶

一個互動式的網頁應用程式，呈現台灣威權時代政治受難者的故事，讓歷史不被遺忘。

![Project Status](https://img.shields.io/badge/status-in%20development-yellow)
![License](https://img.shields.io/badge/license-MIT-blue)

## 📖 專案緣起

這個專案的起源是因為發現大家只知道廣為人知的故事，但其實自己家鄉附近可能有很多相關故事卻不知道。在大學做報告時，意外發現自己家鄉的白恐故事，即使那份報告原本是眷村踏查，與白恐無關。

透過這個互動式地圖，希望能讓更多人了解自己家鄉的歷史，讓這些故事不被遺忘。

## ✨ 功能特色

- 🗺️ **互動式台灣地圖** - 直觀地探索各地的歷史故事
- 📍 **故事標記點** - 每個點代表一個受難者的故事
- 📖 **豐富內容** - 詳細的故事敘述與歷史背景
- 🎥 **多媒體支援** - 圖片、影片、口述歷史音訊
- 🔍 **搜尋與篩選** - 依地區、年代、類型尋找故事（開發中）
- 📱 **響應式設計** - 支援手機、平板、電腦

## 🚀 快速開始

### 前置需求

- Node.js >= 18.0.0
- npm >= 9.0.0

### 安裝與執行

```bash
# 1. Clone 專案
git clone https://github.com/your-username/injustice_story_map.git
cd injustice_story_map

# 2. 安裝依賴
npm install

# 3. 啟動開發伺服器
npm run dev

# 4. 開啟瀏覽器訪問
# http://localhost:5173
```

### 其他指令

```bash
# 建置生產版本
npm run build

# 預覽生產版本
npm run preview

# 執行 Lint 檢查
npm run lint
```

## 📁 專案結構

```
injustice_story_map/
│
├── docs/                        # 📚 專案文件
│   ├── PROJECT_PLAN.md         # 完整專案計畫
│   ├── STORY_COLLECTION_GUIDE.md   # 故事蒐集指南
│   ├── TECHNICAL_SPECS.md      # 技術規格文件
│   └── RECRUITMENT.md          # 招募說明
│
├── public/                      # 🖼️ 靜態資源
│   └── assets/                 # 圖片、影片等
│
├── src/
│   ├── components/             # ⚛️ React 組件
│   │   ├── common/            # 通用組件
│   │   ├── layout/            # 佈局組件（Header, Footer 等）
│   │   ├── map/               # 地圖相關組件
│   │   └── story/             # 故事展示組件
│   │
│   ├── data/                   # 📊 資料檔案
│   │   └── stories.ts         # 故事資料
│   │
│   ├── hooks/                  # 🪝 自訂 Hooks
│   ├── types/                  # 📝 TypeScript 型別定義
│   ├── utils/                  # 🛠️ 工具函式
│   ├── styles/                 # 🎨 樣式檔案
│   │
│   ├── App.tsx                 # 主應用程式
│   └── main.tsx                # 入口檔案
│
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 🛠️ 技術棧

- **前端框架**: React 18 + TypeScript
- **建置工具**: Vite
- **地圖**: Leaflet + React Leaflet
- **樣式**: Tailwind CSS
- **部署**: Vercel / Netlify / GitHub Pages

## 🤝 如何貢獻

我們歡迎各種形式的貢獻！

### 貢獻故事內容

如果你知道更多的不義遺址故事，歡迎提供：

1. 閱讀 [`docs/STORY_COLLECTION_GUIDE.md`](docs/STORY_COLLECTION_GUIDE.md)
2. 按照指南整理故事資料
3. 提交 Issue 或 Pull Request

### 參與開發

1. Fork 本專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 建立 Pull Request

### 加入團隊

我們正在招募：
- 前端工程師
- UI/UX 設計師
- 歷史研究員
- 田野調查員
- 內容編輯
- 社群經營

詳見 [`docs/RECRUITMENT.md`](docs/RECRUITMENT.md)

## 📚 相關文件

- [專案計畫書](docs/PROJECT_PLAN.md) - 完整的專案規劃與團隊分工
- [故事蒐集指南](docs/STORY_COLLECTION_GUIDE.md) - 如何蒐集與提交故事
- [技術規格文件](docs/TECHNICAL_SPECS.md) - 給開發者的技術細節
- [招募說明](docs/RECRUITMENT.md) - 加入我們的團隊

## 🗺️ 路線圖

### 第一階段（已完成 ✅）
- [x] 建立專案基礎架構
- [x] 實作互動式地圖
- [x] 完成故事展示介面
- [x] 加入範例故事資料

### 第二階段（進行中 🚧）
- [ ] 蒐集更多故事（目標：30-50 個）
- [ ] 實作搜尋與篩選功能
- [ ] 加入時間軸功能
- [ ] UI/UX 優化

### 第三階段（規劃中 📋）
- [ ] 建立後端 API
- [ ] 實作使用者投稿系統
- [ ] 多語言支援
- [ ] 社群分享功能

## 📄 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 檔案

## 💬 聯絡我們

- **Email**: [待補充]
- **Facebook**: [待補充]
- **Instagram**: [待補充]
- **GitHub Issues**: [提出問題或建議](https://github.com/your-username/injustice_story_map/issues)

## 🙏 致謝

- 感謝所有受難者與家屬願意分享故事
- 感謝國家人權博物館提供的資源
- 感謝所有貢獻者的付出

---

**「認識歷史，才能理解現在，展望未來。」**

讓我們一起保存這些珍貴的歷史記憶 ❤️
