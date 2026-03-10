# 台灣政治受難事件故事地圖

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
- 🔗 **官方資料連結** - 連結至國家人權博物館、國史館等官方資料來源
- 📱 **響應式設計** - 支援手機、平板、電腦
- 💬 **使用者貢獻** - 歡迎提供新的故事資料

## 🗺️ 目前收錄的故事

本專案目前收錄 12 個歷史事件，時間跨度從 1947 年二二八事件到 1991 年獨台會事件：

- 二二八事件（台北天馬茶房）
- 高雄蕭朝金牧師事件
- 高雄余仁德、劉丁居事件
- 台南吳麗水事件（台南郵電支部案）
- 台北林家血案
- 台南湯德章事件
- 澎湖七一三事件
- 高雄吳某守與李順法案
- 台南陳欽生事件（馬來西亞僑生）
- 新竹獨台會事件
- 台北台灣獨立建國聯盟案

所有故事內容皆基於國家人權博物館、國史館、法務部等官方資料來源，確保歷史事實的準確性。

## 🚀 快速開始

### 前置需求

- Node.js >= 18.0.0
- npm >= 9.0.0

### 安裝與執行

```bash
# 1. Clone 專案
git clone https://github.com/EntropiaTsai/injustice-story-map.git
cd injustice-story-map

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
injustice-story-map/
│
├── public/                      # 🖼️ 靜態資源
│   └── assets/                 # 圖片、影片等
│
├── src/
│   ├── components/             # ⚛️ React 組件
│   │   ├── layout/            # 佈局組件（Header, AboutModal 等）
│   │   ├── map/               # 地圖相關組件
│   │   ├── story/             # 故事展示組件
│   │   └── ContributeModal.tsx # 使用者貢獻介面
│   │
│   ├── data/                   # 📊 資料檔案
│   │   └── stories.ts         # 故事資料（基於官方資料來源）
│   │
│   ├── types/                  # 📝 TypeScript 型別定義
│   ├── utils/                  # 🛠️ 工具函式
│   │   └── mapStyles.ts       # 地圖樣式設定
│   │
│   ├── App.tsx                 # 主應用程式
│   ├── main.tsx                # 入口檔案
│   └── index.css               # 全域樣式
│
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

## 🛠️ 技術棧

- **前端框架**: React 18 + TypeScript
- **建置工具**: Vite
- **地圖**: Leaflet + React Leaflet
- **樣式**: Tailwind CSS
- **部署**: Vercel
- **地圖圖資**: Google Maps (vintage style)

## 🤝 如何貢獻

我們歡迎各種形式的貢獻！

### 貢獻故事內容

如果你知道更多的政治受難事件故事，歡迎透過網站上的「貢獻故事」功能提供資料：

1. 點擊網站右上角的「貢獻故事」按鈕
2. 填寫受難者資料、事件地點、年代
3. 提供相關文章連結或影片連結（官方資料來源優先）
4. 提交後我們會審核並整合至地圖

**重要**：所有故事內容必須基於可驗證的資料來源（如國家人權博物館、國史館、法務部等官方文獻），不接受個人推論或情感描述。

### 參與開發

1. Fork 本專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 建立 Pull Request

## 📚 資料來源

本專案所有故事內容皆基於以下官方資料來源：

- [國家人權博物館 - 國家人權記憶庫](https://memory.nhrm.gov.tw/)
- [國史館檔案史料文物查詢系統](https://aa.archives.gov.tw/)
- [法務部 - 平復司法不法](https://www.moj.gov.tw/)
- [台灣轉型正義資料庫](https://twtjdb.nhrm.gov.tw/)
- [二二八事件紀念基金會](https://www.228.org.tw/)
- [監察院調查報告](https://www.cy.gov.tw/)

## 🗺️ 開發路線圖

### 第一階段（已完成 ✅）
- [x] 建立專案基礎架構
- [x] 實作互動式地圖
- [x] 完成故事展示介面
- [x] 整合 12 個官方驗證的歷史事件
- [x] 實作使用者貢獻介面

### 第二階段（進行中 🚧）
- [ ] 蒐集更多故事（目標：30-50 個）
- [ ] 實作搜尋與篩選功能
- [ ] 加入時間軸功能
- [ ] UI/UX 優化

### 第三階段（規劃中 📋）
- [ ] 建立後端 API
- [ ] 整合 LLM 處理使用者投稿
- [ ] 實作審核機制
- [ ] 社群分享功能

## 📄 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 檔案

## 💬 聯絡方式

- **GitHub Issues**: [提出問題或建議](https://github.com/EntropiaTsai/injustice-story-map/issues)

## 🙏 致謝

- 感謝所有受難者與家屬願意分享故事
- 感謝國家人權博物館、國史館提供的公開資料
- 感謝所有貢獻者的付出

---

**「認識歷史，才能理解現在，展望未來。」**

讓我們一起保存這些珍貴的歷史記憶 ❤️
