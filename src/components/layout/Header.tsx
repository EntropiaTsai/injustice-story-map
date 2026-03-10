import { useState } from 'react';

interface HeaderProps {
  onAboutClick: () => void;
  onContributeClick: () => void;
}

export default function Header({ onAboutClick, onContributeClick }: HeaderProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 bg-white shadow-md z-[1000]">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo 與標題 */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-800 rounded-lg flex items-center justify-center">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-xl md:text-2xl font-bold text-gray-900">
                台灣政治受難事件故事地圖
              </h1>
              <p className="text-xs md:text-sm text-gray-600 hidden sm:block">
                探索你家鄉的歷史記憶
              </p>
            </div>
          </div>

          {/* 桌面版選單 */}
          <nav className="hidden md:flex items-center gap-6">
            <button
              onClick={onAboutClick}
              className="text-gray-700 hover:text-blue-600 font-medium transition-colors"
            >
              關於專案
            </button>
            <button
              onClick={onContributeClick}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              貢獻故事
            </button>
          </nav>

          {/* 手機版選單按鈕 */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="選單"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              {isMenuOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </div>

        {/* 手機版下拉選單 */}
        {isMenuOpen && (
          <nav className="md:hidden mt-4 pt-4 border-t border-gray-200">
            <div className="flex flex-col gap-3">
              <button
                onClick={() => {
                  onAboutClick();
                  setIsMenuOpen(false);
                }}
                className="text-left py-2 px-4 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                關於專案
              </button>
              <button
                onClick={() => {
                  onContributeClick();
                  setIsMenuOpen(false);
                }}
                className="text-left py-2 px-4 bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors font-medium"
              >
                ➕ 貢獻故事
              </button>
            </div>
          </nav>
        )}
      </div>
    </header>
  );
}
