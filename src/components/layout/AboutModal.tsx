interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AboutModal({ isOpen, onClose }: AboutModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[2000] flex items-center justify-center p-4">
      {/* 背景遮罩 */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />

      {/* 彈出視窗 */}
      <div className="relative bg-white rounded-lg shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* 關閉按鈕 */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full bg-gray-800 hover:bg-gray-900 text-white transition-colors shadow-lg"
          aria-label="關閉"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        {/* 內容 */}
        <div className="p-8">
          <h2 className="text-3xl font-bold mb-6 text-gray-900">
            關於本專案
          </h2>

          <div className="space-y-6 text-gray-700 leading-relaxed">
            <section>
              <h3 className="text-xl font-bold mb-3 text-gray-900">專案緣起</h3>
              <p>
                大學時，為了一份地方踏查報告，我重新走進自己從小長大的街道。原本關心的是日常生活與空間記憶，但在查資料的過程中，我卻第一次知道——這些再熟悉不過的地方，曾經發生過白色恐怖事件。
              </p>
              <p className="mt-2">
                那一刻我才意識到，白色恐怖不只是歷史課本上的名詞。那些政治受難的故事，也不只存在於被反覆提及的幾個案件，而是真實地發生在我們生活的城市裡。
              </p>
              <p className="mt-2">
                這樣的經驗並不特別。在台灣各地，仍有許多事件散落在地方文史、檔案或記憶之中，沒有被系統性地看見，也很少被重新連結回它們發生的地方。
              </p>
              <p className="mt-2">
                歷史從來不只存在於課本或紀念館，它其實就藏在我們每天經過的街道、建築與地景之中。
              </p>
              <p className="mt-2">
                這個地圖專案，試圖將這些分散的故事重新標記在它們發生的位置，讓人們在經過時，不只是經過，而是能重新看見、重新理解這些地方曾經承載的歷史。
              </p>
            </section>

            <section>
              <h3 className="text-xl font-bold mb-3 text-gray-900">專案目標</h3>
              <ul className="list-disc list-inside space-y-2">
                <li>透過互動式地圖，讓人們更容易發現自己家鄉的歷史故事</li>
                <li>保存並傳承政治受難者的記憶，讓這些故事不被遺忘</li>
                <li>促進轉型正義教育，提醒我們珍惜得來不易的民主自由</li>
                <li>建立一個開放的平台，讓更多人能夠貢獻和分享故事</li>
              </ul>
            </section>

            <section>
              <h3 className="text-xl font-bold mb-3 text-gray-900">如何使用</h3>
              <ol className="list-decimal list-inside space-y-2">
                <li>在地圖上尋找你感興趣的地點（藍色標記點）</li>
                <li>點擊標記點查看該地點的簡要資訊</li>
                <li>點擊「查看完整故事」按鈕，閱讀詳細的故事內容</li>
                <li>透過影音資料，更深入了解受難者的經歷</li>
              </ol>
            </section>

            <section>
              <h3 className="text-xl font-bold mb-3 text-gray-900">貢獻故事</h3>
              <p>
                如果你知道更多的政治受難事件故事，或者你家鄉有相關的歷史記憶，歡迎與我們分享。每一個故事都很重要，每一份記憶都值得被保存。
              </p>
              <p className="mt-2">
                你可以透過 GitHub 或聯絡我們，提供相關的資料、照片、影音檔案等。讓我們一起完善這份地圖，讓更多人認識台灣的歷史。
              </p>
            </section>

            <section>
              <h3 className="text-xl font-bold mb-3 text-gray-900">技術資訊</h3>
              <p>
                本專案使用 React、TypeScript、Leaflet 等現代化網頁技術建構，是一個開源專案。
              </p>
              <p className="mt-2">
                程式碼託管於 GitHub，歡迎開發者一同參與改進。
              </p>
            </section>

            <section className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
              <p className="font-medium text-gray-900">
                「認識歷史，才能理解現在，展望未來。」
              </p>
              <p className="mt-2 text-sm">
                希望這個專案能讓更多人了解台灣的歷史，珍惜民主自由的價值。
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
