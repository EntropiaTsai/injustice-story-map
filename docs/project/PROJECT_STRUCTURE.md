# 專案結構說明

## 📂 完整目錄樹

```
injustice_story_map/
│
├── 📚 docs/                          專案文件目錄（詳見 docs/README.md）
│   ├── README.md                    文件索引
│   ├── project/                     計畫、架構、技術、招募
│   │   ├── PROJECT_PLAN.md
│   │   ├── PROJECT_STRUCTURE.md     專案結構說明（本文件）
│   │   ├── TECHNICAL_SPECS.md
│   │   └── RECRUITMENT.md
│   ├── guides/                      故事蒐集與內容操作指南
│   ├── agents/                      編輯流程 Agent／Gemini prompt
│   └── research/                    研究參考、名單、個案筆記
│
├── 🌐 public/                        靜態資源目錄
│   └── assets/                      圖片、影片等多媒體檔案
│
├── 💻 src/                           原始碼目錄
│   │
│   ├── 🧩 components/               React 組件
│   │   ├── common/                  通用組件（按鈕、Modal 等）
│   │   ├── layout/                  佈局組件
│   │   │   ├── Header.tsx          頁首導覽列
│   │   │   └── AboutModal.tsx      關於專案彈窗
│   │   ├── map/                     地圖相關組件
│   │   │   └── MapView.tsx         主地圖視圖
│   │   └── story/                   故事展示組件
│   │       └── StorySidebar.tsx    故事側邊欄
│   │
│   ├── 📊 data/                     資料檔案
│   │   └── stories.ts              故事資料（目前為靜態 JSON）
│   │
│   ├── 🪝 hooks/                    自訂 React Hooks
│   │   （目前為空，未來可加入）
│   │
│   ├── 📝 types/                    TypeScript 型別定義
│   │   └── index.ts                所有型別定義（StoryLocation 等）
│   │
│   ├── 🛠️ utils/                    工具函式
│   │   （目前為空，未來可加入）
│   │
│   ├── 🎨 styles/                   樣式檔案
│   │   └── index.css               全域樣式與 Tailwind
│   │
│   ├── App.tsx                      主應用程式組件
│   └── main.tsx                     應用程式入口點
│
├── 📋 根目錄設定檔（必須保留）
│   ├── package.json                 專案依賴與指令
│   ├── tsconfig.json               TypeScript 設定
│   ├── tsconfig.node.json          Node TypeScript 設定
│   ├── vite.config.ts              Vite 建置工具設定
│   ├── tailwind.config.js          Tailwind CSS 設定
│   ├── postcss.config.js           PostCSS 設定
│   └── env.example                 環境變數範例
│
├── 🌍 index.html                    HTML 模板
├── 📖 README.md                     專案說明文件
├── 📘 ROOT_FILES_EXPLANATION.md     根目錄檔案說明
└── .gitignore                       Git 忽略規則
```

---

## 📁 目錄說明

### `/docs` - 文件目錄
依子資料夾分類：`project/`（計畫與技術）、`guides/`（內容指南）、`agents/`（自動化 prompt）、`research/`（研究參考）。**入口**：`docs/README.md`。

**特點**：
- 所有成員都應該閱讀這些文件
- 依角色選擇適合的文件
- 隨專案進展持續更新

---

### `/public` - 公開靜態資源
存放不需要經過建置的靜態檔案。

**使用時機**：
- 圖片、影片、音訊等多媒體檔案
- favicon、robots.txt 等靜態資源
- 這些檔案會直接複製到建置輸出目錄

**檔案引用方式**：
```tsx
// 直接使用絕對路徑
<img src="/assets/images/photo.jpg" />
```

---

### `/src/components` - React 組件

#### `/common` - 通用組件
可重複使用的基礎組件，例如：
- Button 按鈕
- Modal 彈出視窗
- Loading 載入動畫
- Input 輸入框

#### `/layout` - 佈局組件
頁面結構相關的組件，例如：
- Header 頁首
- Footer 頁尾
- Sidebar 側邊欄
- Navigation 導覽列

#### `/map` - 地圖組件
地圖功能相關的組件，例如：
- MapView 地圖視圖
- StoryMarker 故事標記
- MapControls 地圖控制項

#### `/story` - 故事組件
故事內容展示相關的組件，例如：
- StorySidebar 故事側邊欄
- StoryCard 故事卡片
- StoryDetail 故事詳情
- MediaGallery 媒體畫廊

---

### `/src/data` - 資料檔案
存放應用程式的資料。

**目前狀態**：
- `stories.ts` - 靜態故事資料（範例）

**未來規劃**：
- 改為從 API 載入資料
- 或使用 JSON 檔案管理

---

### `/src/hooks` - 自訂 Hooks
存放自訂的 React Hooks，提高程式碼重用性。

**未來可能加入**：
```typescript
useStories.ts    // 處理故事資料
useMap.ts        // 地圖控制邏輯
useSearch.ts     // 搜尋功能
useFilter.ts     // 篩選功能
```

---

### `/src/types` - 型別定義
集中管理 TypeScript 型別定義。

**好處**：
- 統一型別定義
- 避免重複
- 易於維護

**目前定義**：
```typescript
StoryLocation    // 故事地點型別
StoryCategory    // 故事分類枚舉
```

---

### `/src/utils` - 工具函式
存放可重複使用的工具函式。

**未來可能加入**：
```typescript
api.ts           // API 請求封裝
format.ts        // 格式化函式（日期、文字等）
validation.ts    // 驗證函式
constants.ts     // 常數定義
```

---

### `/src/styles` - 樣式檔案
存放全域樣式和 CSS 設定。

**目前內容**：
- `index.css` - 全域樣式、Tailwind directives、Leaflet 樣式調整

---

## 🎯 檔案命名規範

### 組件檔案
- **格式**: `PascalCase.tsx`
- **範例**: `MapView.tsx`, `StorySidebar.tsx`

### 工具函式
- **格式**: `camelCase.ts`
- **範例**: `formatDate.ts`, `apiClient.ts`

### 型別定義
- **格式**: `camelCase.ts` 或 `index.ts`
- **範例**: `story.ts`, `user.ts`, `index.ts`

### 樣式檔案
- **格式**: `kebab-case.css` 或 `camelCase.css`
- **範例**: `index.css`, `custom-styles.css`

---

## 🔄 如何新增功能

### 1. 新增一個組件

```bash
# 選擇適當的目錄
src/components/
├── common/      # 如果是通用組件
├── layout/      # 如果是佈局組件
├── map/         # 如果是地圖相關
└── story/       # 如果是故事相關

# 建立檔案
src/components/story/StoryCard.tsx
```

### 2. 新增自訂 Hook

```bash
# 在 hooks 目錄建立
src/hooks/useStories.ts
```

### 3. 新增型別定義

```bash
# 在 types 目錄建立或更新
src/types/index.ts
```

### 4. 新增工具函式

```bash
# 在 utils 目錄建立
src/utils/formatDate.ts
```

---

## 📦 Import 路徑規範

### 使用相對路徑

```typescript
// 從 src/components/story/StoryCard.tsx
import { StoryLocation } from '../../types';
import { formatDate } from '../../utils/formatDate';
```

### 路徑別名（可選，未來設定）

```typescript
// 未來可以使用路徑別名
import { StoryLocation } from '@/types';
import { formatDate } from '@/utils/formatDate';
```

---

## 🚀 開發工作流程

1. **開發新功能**
   ```bash
   # 建立功能分支
   git checkout -b feature/new-feature
   
   # 在對應目錄建立檔案
   # 開發、測試
   
   # 提交變更
   git commit -m "feat: add new feature"
   ```

2. **更新文件**
   - 如果新增重要功能，更新 `README.md`
   - 如果影響團隊協作，更新 `docs/` 中的相關文件

3. **保持整潔**
   - 定期清理未使用的檔案
   - 遵循命名規範
   - 適當的程式碼註解

---

## 💡 最佳實踐

### 組件組織
- 每個組件一個檔案
- 相關組件放在同一目錄下
- 複雜組件可以建立子目錄

### 程式碼分割
- 使用 React.lazy() 進行路由層級的分割
- 大型組件考慮拆分成小組件

### 型別安全
- 盡量定義明確的型別
- 避免使用 `any`
- 善用 TypeScript 的型別推導

---

**最後更新**: 2026-03-08
