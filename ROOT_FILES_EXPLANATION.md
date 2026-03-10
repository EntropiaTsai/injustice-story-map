# 根目錄檔案說明

根目錄的這些設定檔是標準的專案配置，它們**需要放在根目錄**才能正常運作。

## 📋 設定檔清單

### ⚙️ 建置與開發工具

#### `vite.config.ts` ⭐ 必要
**用途**: Vite 建置工具的設定檔  
**作用**: 
- 設定 React plugin
- 定義建置規則
- 開發伺服器設定

**為何在根目錄**: Vite 預設讀取根目錄的此檔案

---

#### `package.json` ⭐ 必要
**用途**: Node.js 專案設定檔  
**作用**:
- 定義專案依賴套件
- 定義 npm 指令（dev, build 等）
- 專案基本資訊

**為何在根目錄**: npm/yarn 預設讀取根目錄的此檔案

---

### 📝 TypeScript 設定

#### `tsconfig.json` ⭐ 必要
**用途**: TypeScript 主要設定檔  
**作用**:
- TypeScript 編譯選項
- 型別檢查規則
- 模組解析設定

**為何在根目錄**: TypeScript 預設讀取根目錄的此檔案

---

#### `tsconfig.node.json` ⭐ 必要
**用途**: Node.js 環境的 TypeScript 設定  
**作用**:
- 針對 vite.config.ts 等 Node 檔案的設定
- 與主要 tsconfig.json 分離

**為何在根目錄**: 由 tsconfig.json 引用

---

### 🎨 樣式工具

#### `tailwind.config.js` ⭐ 必要
**用途**: Tailwind CSS 設定檔  
**作用**:
- 定義樣式主題
- 設定掃描路徑
- 自訂 utility classes

**為何在根目錄**: Tailwind 預設讀取根目錄的此檔案

---

#### `postcss.config.js` ⭐ 必要
**用途**: PostCSS 處理器設定  
**作用**:
- 整合 Tailwind CSS
- 整合 Autoprefixer

**為何在根目錄**: PostCSS 預設讀取根目錄的此檔案

---

### 🌐 HTML 模板

#### `index.html` ⭐ 必要
**用途**: HTML 入口檔案  
**作用**:
- 應用程式的 HTML 模板
- 載入 React 應用

**為何在根目錄**: Vite 使用根目錄的 index.html 作為入口

---

### 📄 其他檔案

#### `.gitignore` ⭐ 必要
**用途**: Git 忽略規則  
**作用**: 定義哪些檔案不要提交到 Git

**為何在根目錄**: Git 預設讀取根目錄的此檔案

---

#### `env.example` ⚠️ 選用
**用途**: 環境變數範例  
**作用**: 給其他開發者參考需要哪些環境變數

**為何在根目錄**: 慣例放在根目錄，方便複製成 `.env`

---

#### `README.md` ⭐ 必要
**用途**: 專案說明文件  
**作用**: 專案介紹、安裝與使用說明

**為何在根目錄**: GitHub 等平台會顯示根目錄的 README

---

#### `PROJECT_STRUCTURE.md` 📚 文件
**用途**: 專案結構說明  
**作用**: 詳細說明目錄結構

**可以移到 docs/**: 是的！這個可以考慮

---

## ✅ 總結

### 這些檔案**必須**保留在根目錄：
```
injustice_story_map/
├── package.json          ← npm 需要
├── vite.config.ts        ← Vite 需要
├── tsconfig.json         ← TypeScript 需要
├── tsconfig.node.json    ← TypeScript 需要
├── tailwind.config.js    ← Tailwind 需要
├── postcss.config.js     ← PostCSS 需要
├── index.html            ← Vite 入口
├── .gitignore            ← Git 需要
└── env.example           ← 慣例
```

### 這些是文件，可以保持或移動：
```
├── README.md                  ← 慣例放根目錄
└── PROJECT_STRUCTURE.md       ← 可移到 docs/（可選）
```

---

## 🎯 為什麼看起來很多？

這是**現代前端專案的標準配置**，每個檔案都有其用途：

1. **JavaScript 生態**: `package.json`
2. **TypeScript**: `tsconfig.json`, `tsconfig.node.json`
3. **建置工具**: `vite.config.ts`
4. **樣式工具**: `tailwind.config.js`, `postcss.config.js`
5. **版本控制**: `.gitignore`
6. **文件**: `README.md`, `index.html`

---

## 💡 其他專案比較

幾乎所有現代前端專案的根目錄都是這樣的：

```
# Next.js 專案
next.config.js
package.json
tsconfig.json
postcss.config.js
tailwind.config.js

# Vue 專案  
vite.config.ts
package.json
tsconfig.json
vue.config.js

# 我們的專案（已經很精簡了！）
vite.config.ts
package.json
tsconfig.json
tsconfig.node.json
tailwind.config.js
postcss.config.js
```

---

## 🧹 我們已經做的整理

✅ 把文件移到 `docs/`  
✅ 把組件分類到子目錄  
✅ 把型別定義獨立出來  
✅ 把樣式移到 `styles/`  

根目錄的設定檔已經是**最精簡**的狀態了！

---

## 🤔 如果真的想要更乾淨...

### 選項 1: 接受現狀（推薦 ⭐）
這是業界標準，所有開發者都習慣這樣的結構。

### 選項 2: 隱藏設定檔（不推薦）
某些工具允許把設定放在 `package.json` 裡，但會讓設定很難維護。

### 選項 3: Monorepo 架構（過度設計）
使用 pnpm workspace 或 Turborepo，但對這個專案來說太複雜了。

---

**建議**: 根目錄的設定檔保持現狀，它們是必要的工具配置！✨
