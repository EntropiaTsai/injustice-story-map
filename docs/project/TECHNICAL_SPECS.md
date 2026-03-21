# 技術規格文件

本文件提供給**技術開發組**成員，說明專案的技術架構、開發規範和實作細節。

---

## 🏗️ 系統架構

### 整體架構圖

```
┌─────────────────────────────────────────────────────────┐
│                     使用者                               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              前端 (React + TypeScript)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ 地圖介面 │  │故事瀏覽  │  │ 搜尋篩選 │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              API 層 (RESTful / GraphQL)                  │
│                      (可選)                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│        資料層 (靜態 JSON / 資料庫)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ 故事資料 │  │ 媒體檔案 │  │ 使用者資料│             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## 💻 技術堆疊

### 前端

#### 核心框架
- **React 18** - 使用者介面框架
- **TypeScript** - 型別安全
- **Vite** - 建置工具（快速開發體驗）

#### UI 相關
- **Tailwind CSS** - CSS 框架
- **Leaflet** - 地圖套件
- **React Leaflet** - React 地圖組件

#### 狀態管理（按需求選擇）
- 簡單專案：React Context + Hooks
- 複雜專案：Zustand / Redux Toolkit

#### 路由（如需多頁面）
- **React Router** v6

#### 資料請求（如有 API）
- **Axios** 或 **React Query**

### 後端（階段二，可選）

#### 選項一：Node.js
- **Express.js** / **Fastify** - Web 框架
- **PostgreSQL** / **MongoDB** - 資料庫
- **Prisma** / **TypeORM** - ORM

#### 選項二：Python
- **FastAPI** / **Django** - Web 框架
- **PostgreSQL** - 資料庫
- **SQLAlchemy** - ORM

#### 選項三：靜態方案（推薦初期）
- 直接使用靜態 JSON 檔案
- 透過 GitHub Pages 或 Vercel 部署
- 無需後端伺服器

### 部署

#### 前端部署
- **Vercel** (推薦，免費且簡單)
- **Netlify** 
- **GitHub Pages**
- **Cloudflare Pages**

#### 後端部署（如需要）
- **Heroku** (簡單但收費)
- **Railway** (推薦，有免費額度)
- **DigitalOcean** (較專業)
- **AWS** / **GCP** (大規模使用)

#### 媒體檔案儲存
- **Cloudinary** (圖片最佳化)
- **AWS S3** (大量檔案)
- **GitHub** (小型專案)

---

## 📁 專案結構

```
injustice_story_map/
│
├── public/                      # 靜態資源
│   ├── images/                  # 圖片資源
│   ├── videos/                  # 影片資源（或用 CDN）
│   └── favicon.ico
│
├── src/
│   ├── components/              # React 組件
│   │   ├── map/
│   │   │   ├── MapView.tsx     # 地圖主視圖
│   │   │   ├── StoryMarker.tsx # 故事標記
│   │   │   └── MapControls.tsx # 地圖控制項
│   │   │
│   │   ├── story/
│   │   │   ├── StorySidebar.tsx     # 故事側邊欄
│   │   │   ├── StoryCard.tsx        # 故事卡片
│   │   │   ├── StoryDetail.tsx      # 故事詳情
│   │   │   └── MediaGallery.tsx     # 媒體畫廊
│   │   │
│   │   ├── layout/
│   │   │   ├── Header.tsx           # 頁首
│   │   │   ├── Footer.tsx           # 頁尾
│   │   │   └── Navigation.tsx       # 導覽列
│   │   │
│   │   ├── search/
│   │   │   ├── SearchBar.tsx        # 搜尋列
│   │   │   ├── FilterPanel.tsx      # 篩選面板
│   │   │   └── StoryList.tsx        # 故事列表
│   │   │
│   │   └── common/
│   │       ├── Button.tsx           # 按鈕組件
│   │       ├── Modal.tsx            # 彈出視窗
│   │       ├── Loading.tsx          # 載入動畫
│   │       └── ErrorBoundary.tsx    # 錯誤邊界
│   │
│   ├── data/
│   │   ├── stories.ts               # 故事資料（靜態）
│   │   ├── categories.ts            # 分類資料
│   │   └── locations.ts             # 地點資料
│   │
│   ├── hooks/                       # 自訂 Hooks
│   │   ├── useStories.ts           # 故事資料 Hook
│   │   ├── useMap.ts               # 地圖控制 Hook
│   │   └── useSearch.ts            # 搜尋功能 Hook
│   │
│   ├── utils/                       # 工具函式
│   │   ├── api.ts                  # API 請求（如需要）
│   │   ├── format.ts               # 格式化函式
│   │   ├── validation.ts           # 驗證函式
│   │   └── constants.ts            # 常數定義
│   │
│   ├── types/                       # TypeScript 型別定義
│   │   ├── story.ts                # 故事型別
│   │   ├── location.ts             # 地點型別
│   │   └── index.ts                # 匯出所有型別
│   │
│   ├── styles/                      # 樣式檔案
│   │   ├── index.css               # 全域樣式
│   │   └── tailwind.css            # Tailwind 設定
│   │
│   ├── App.tsx                      # 主應用程式
│   └── main.tsx                     # 入口檔案
│
├── docs/                            # 文件（見 docs/README.md）
│   ├── project/                     # 計畫、技術規格等
│   ├── guides/                      # 故事蒐集指南等
│   ├── agents/                      # Agent／Gemini prompt
│   └── research/                    # 研究參考
│
├── tests/                           # 測試檔案
│   ├── unit/                       # 單元測試
│   └── integration/                # 整合測試
│
├── .github/                         # GitHub 設定
│   └── workflows/                  # CI/CD 設定
│
├── package.json                     # 專案依賴
├── tsconfig.json                    # TypeScript 設定
├── tailwind.config.js              # Tailwind 設定
├── vite.config.ts                  # Vite 設定
├── .gitignore
├── .env.example                     # 環境變數範例
└── README.md
```

---

## 🔧 開發環境設置

### 前置需求
- Node.js >= 18.0.0
- npm >= 9.0.0 或 yarn >= 1.22.0
- Git
- VS Code（推薦）

### 初始化專案

```bash
# 1. Clone 專案
git clone https://github.com/your-username/injustice_story_map.git
cd injustice_story_map

# 2. 安裝依賴
npm install

# 3. 複製環境變數檔案
cp .env.example .env

# 4. 啟動開發伺服器
npm run dev

# 5. 開啟瀏覽器訪問
# http://localhost:5173
```

### VS Code 推薦擴充套件

```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-typescript-next",
    "formulahendry.auto-rename-tag",
    "dsznajder.es7-react-js-snippets"
  ]
}
```

### 程式碼格式化設定

`.prettierrc`
```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

---

## 📊 資料結構

### Story（故事）型別定義

```typescript
interface StoryLocation {
  // 基本資訊
  id: string;                    // 唯一識別碼
  name: string;                  // 地點名稱
  victimName: string;            // 受難者姓名
  
  // 地理資訊
  lat: number;                   // 緯度
  lng: number;                   // 經度
  address?: string;              // 詳細地址
  
  // 時間資訊
  year: string;                  // 年份（可以是範圍，如 "1950-1954"）
  
  // 內容資訊
  title: string;                 // 故事標題
  summary: string;               // 摘要（100-150字）
  content: string;               // 完整內容（支援 Markdown）
  
  // 多媒體
  images?: string[];             // 圖片 URLs
  videos?: string[];             // 影片 URLs
  audioUrl?: string;             // 音訊 URL
  
  // 延伸資料
  relatedLinks?: {
    title: string;
    url: string;
  }[];
  
  // 分類與標籤
  tags?: string[];               // 標籤（如：白色恐怖、台北市）
  category?: StoryCategory;      // 分類
  
  // 元資料
  createdAt?: string;            // 建立日期
  updatedAt?: string;            // 更新日期
  contributor?: string;          // 貢獻者
  sources?: string[];            // 資料來源
  
  // 狀態
  status?: 'draft' | 'published' | 'archived';
}
```

### Category（分類）型別

```typescript
enum StoryCategory {
  Prison = 'prison',              // 監獄
  ExecutionGround = 'execution',  // 刑場
  Cemetery = 'cemetery',          // 墓地
  Court = 'court',                // 審判地
  Memorial = 'memorial',          // 紀念地
  Historical = 'historical',      // 歷史建築
  Other = 'other'                 // 其他
}
```

---

## 🎨 設計系統

### 色彩規範

```css
/* 主色調 */
--primary-50: #f0f9ff;
--primary-100: #e0f2fe;
--primary-500: #0ea5e9;  /* 主要藍色 */
--primary-700: #0369a1;

/* 輔助色 */
--secondary-500: #6366f1;  /* 紫色 */
--accent-500: #f59e0b;     /* 橙色 */

/* 灰階 */
--gray-50: #f9fafb;
--gray-100: #f3f4f6;
--gray-500: #6b7280;
--gray-900: #111827;

/* 語意色 */
--success: #10b981;  /* 綠色 */
--warning: #f59e0b;  /* 橙色 */
--error: #ef4444;    /* 紅色 */
--info: #3b82f6;     /* 藍色 */
```

### 字體規範

```css
/* 字體家族 */
font-family: 'Noto Sans TC', Inter, system-ui, sans-serif;

/* 字體大小 */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
```

### 間距規範

使用 Tailwind 預設間距（4px 基準）
- `p-1` = 4px
- `p-2` = 8px
- `p-4` = 16px
- `p-6` = 24px
- `p-8` = 32px

### 圓角規範

```css
--rounded-sm: 0.125rem;   /* 2px */
--rounded: 0.25rem;       /* 4px */
--rounded-md: 0.375rem;   /* 6px */
--rounded-lg: 0.5rem;     /* 8px */
--rounded-xl: 0.75rem;    /* 12px */
--rounded-2xl: 1rem;      /* 16px */
```

---

## 🗺️ 地圖功能規格

### 基本功能

1. **地圖顯示**
   - 使用 OpenStreetMap 作為底圖
   - 中心點：台灣中心（23.5°N, 121°E）
   - 初始縮放級別：8
   - 支援縮放、拖曳、雙指手勢

2. **標記點（Markers）**
   - 自訂圖標（藍色圓點）
   - 選中時變為紅色
   - Hover 時顯示提示
   - 點擊後顯示詳細資訊

3. **Popup（彈出視窗）**
   - 顯示故事摘要
   - 「查看完整故事」按鈕
   - 自動調整位置避免超出邊界

4. **地圖控制項**
   - 縮放按鈕
   - 全螢幕按鈕
   - 重置視圖按鈕
   - 圖層切換（如有多個底圖）

### 進階功能（階段二）

1. **群集（Clustering）**
   - 當標記點過於密集時自動群集
   - 顯示數量
   - 點擊後放大

2. **熱力圖（Heatmap）**
   - 視覺化呈現事件密度
   - 可切換顯示/隱藏

3. **時間軸**
   - 依年代篩選故事
   - 動畫播放歷史事件

4. **路徑規劃**
   - 規劃參觀路線
   - 匯出路線

---

## 🔍 搜尋與篩選規格

### 搜尋功能

```typescript
interface SearchParams {
  keyword?: string;        // 關鍵字搜尋
  tags?: string[];         // 標籤篩選
  category?: StoryCategory; // 分類篩選
  yearFrom?: number;       // 年份範圍（起）
  yearTo?: number;         // 年份範圍（迄）
  location?: string;       // 地點篩選
  sortBy?: 'date' | 'name' | 'relevance'; // 排序方式
}
```

### 實作建議

```typescript
// 使用 Fuse.js 進行模糊搜尋
import Fuse from 'fuse.js';

const fuse = new Fuse(stories, {
  keys: ['title', 'summary', 'content', 'victimName', 'tags'],
  threshold: 0.3,
});

const searchResults = fuse.search(keyword);
```

---

## 📱 響應式設計

### 斷點定義

```css
/* Tailwind 預設斷點 */
sm: 640px   /* 手機橫向 */
md: 768px   /* 平板直向 */
lg: 1024px  /* 平板橫向 */
xl: 1280px  /* 桌面 */
2xl: 1536px /* 大螢幕 */
```

### 佈局策略

#### 手機版（< 768px）
- 全螢幕地圖
- 側邊欄改為全螢幕彈出
- Header 簡化（漢堡選單）
- 單欄佈局

#### 平板版（768px - 1024px）
- 地圖 + 側邊欄（可收合）
- Header 顯示主要功能
- 部分雙欄佈局

#### 桌面版（> 1024px）
- 完整功能顯示
- 固定側邊欄
- 多欄佈局

---

## ⚡ 效能優化

### 圖片優化

1. **使用適當格式**
   - 照片：JPEG（品質 80-85%）
   - 圖示/插圖：WebP
   - 透明背景：PNG

2. **響應式圖片**
   ```html
   <img 
     srcset="image-400.jpg 400w, image-800.jpg 800w"
     sizes="(max-width: 768px) 400px, 800px"
     src="image-800.jpg"
     alt="描述"
   />
   ```

3. **延遲載入**
   ```html
   <img loading="lazy" src="image.jpg" alt="描述" />
   ```

### 程式碼分割

```typescript
// 路由層級的程式碼分割
const StoryDetail = lazy(() => import('./components/story/StoryDetail'));
const SearchPage = lazy(() => import('./pages/SearchPage'));

// 使用 Suspense
<Suspense fallback={<Loading />}>
  <StoryDetail />
</Suspense>
```

### 地圖效能

1. **限制可見標記數量**
   - 根據縮放級別顯示標記
   - 使用群集功能

2. **防抖（Debounce）**
   ```typescript
   const handleMapMove = debounce(() => {
     // 更新可見標記
   }, 200);
   ```

---

## 🧪 測試策略

### 單元測試

使用 Vitest + React Testing Library

```typescript
// 範例：測試 StoryCard 組件
import { render, screen } from '@testing-library/react';
import StoryCard from './StoryCard';

test('renders story card with correct information', () => {
  const story = {
    id: '1',
    title: '測試故事',
    summary: '這是摘要',
    // ...
  };
  
  render(<StoryCard story={story} />);
  
  expect(screen.getByText('測試故事')).toBeInTheDocument();
  expect(screen.getByText('這是摘要')).toBeInTheDocument();
});
```

### E2E 測試（可選）

使用 Playwright 或 Cypress

```typescript
// 範例：測試完整用戶流程
test('user can view story details', async ({ page }) => {
  await page.goto('http://localhost:5173');
  await page.click('[data-story-id="1"]');
  await expect(page.locator('.story-sidebar')).toBeVisible();
});
```

---

## 🚀 部署流程

### 使用 Vercel（推薦）

1. **連結 GitHub**
   - 登入 Vercel
   - 匯入 GitHub repository
   - Vercel 會自動偵測 Vite 專案

2. **設定環境變數**
   ```
   VITE_API_URL=https://api.example.com
   VITE_MAP_TOKEN=your_token_here
   ```

3. **自動部署**
   - 推送到 main 分支 → 自動部署到 Production
   - 推送到其他分支 → 自動建立 Preview

### 使用 GitHub Pages

```bash
# 1. 安裝 gh-pages
npm install --save-dev gh-pages

# 2. 在 package.json 加入
{
  "scripts": {
    "deploy": "vite build && gh-pages -d dist"
  }
}

# 3. 執行部署
npm run deploy
```

---

## 📝 開發規範

### Git 工作流程

```bash
# 1. 從 main 分支建立功能分支
git checkout -b feature/story-sidebar

# 2. 開發與提交
git add .
git commit -m "feat: add story sidebar component"

# 3. 推送到遠端
git push origin feature/story-sidebar

# 4. 建立 Pull Request
# 在 GitHub 上建立 PR，等待審核

# 5. 合併後刪除分支
git branch -d feature/story-sidebar
```

### Commit 訊息規範

使用 Conventional Commits

```
feat: 新功能
fix: 修復 Bug
docs: 文件更新
style: 程式碼格式調整
refactor: 重構
test: 測試相關
chore: 建置工具或輔助工具的變動

範例：
feat: add search functionality
fix: correct marker position on mobile
docs: update API documentation
```

### 程式碼審查清單

- [ ] 程式碼符合專案風格
- [ ] 無 console.log 或調試程式碼
- [ ] 型別定義完整
- [ ] 有適當的錯誤處理
- [ ] 有必要的註解
- [ ] 通過 ESLint 檢查
- [ ] 響應式設計正確
- [ ] 效能無明顯問題

---

## 🔒 安全性考量

### 前端安全

1. **XSS 防護**
   - 使用 React 的自動跳脫
   - 危險的 HTML 使用 DOMPurify

2. **CSRF 防護**
   - API 請求使用 Token

3. **資料驗證**
   - 前後端都要驗證
   - 使用 Zod 或 Yup 進行驗證

### 環境變數

```env
# .env.example
VITE_API_URL=https://api.example.com
VITE_MAP_TOKEN=your_token_here

# 注意：VITE_ 開頭的變數會暴露在前端
# 敏感資訊不要用 VITE_ 開頭
```

---

## 📚 相關資源

### 官方文件
- [React 文件](https://react.dev/)
- [TypeScript 文件](https://www.typescriptlang.org/)
- [Leaflet 文件](https://leafletjs.com/)
- [Tailwind CSS 文件](https://tailwindcss.com/)

### 學習資源
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [Leaflet 教學](https://leafletjs.com/examples.html)

---

## 📞 技術支援

如有技術問題，歡迎聯繫：
- GitHub Issues
- Discord 技術頻道
- Email（待補充）

---

**最後更新：** 2026-03-08  
**版本：** 1.0  
**維護者：** 開發組
