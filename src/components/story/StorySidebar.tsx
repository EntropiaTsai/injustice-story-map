import type { StoryLocation } from '../../types';

interface StorySidebarProps {
  story: StoryLocation | null;
  onClose: () => void;
  isOpen: boolean;
  onContribute?: (storyId: string) => void;
}

export default function StorySidebar({ story, onClose, isOpen, onContribute }: StorySidebarProps) {
  if (!isOpen || !story) return null;

  const handleContribute = () => {
    if (onContribute && story) {
      onContribute(story.id);
    }
  };

  return (
    <>
      {/* 背景遮罩 - 手機版 */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-[1001] md:hidden"
        onClick={onClose}
      />
      
      {/* 側邊欄 */}
      <div
        className={`
          fixed top-0 right-0 h-full w-full md:w-[480px] lg:w-[560px]
          bg-white shadow-2xl z-[1002]
          transform transition-transform duration-300 ease-in-out
          overflow-y-auto
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}
        `}
      >
        {/* 關閉按鈕 */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full bg-gray-800 hover:bg-gray-900 text-white transition-colors z-10 shadow-lg"
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

        {/* 內容區 */}
        <div className="p-6 md:p-8">
          {/* 標題區 */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                {story.year}
              </span>
            </div>
            <h2 className="text-3xl font-bold mb-2 text-gray-900">
              {story.title}
            </h2>
            <h3 className="text-xl text-gray-600 mb-2">
              {story.name}
            </h3>
            <p className="text-lg text-gray-700 font-medium">
              受難者：{story.victimName}
            </p>
          </div>

          {/* 摘要 */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg border-l-4 border-blue-500">
            <p className="text-gray-700 leading-relaxed">
              {story.summary}
            </p>
          </div>

          {/* 標籤 */}
          {story.tags && story.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-6">
              {story.tags.map((tag, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-gray-200 text-gray-700 rounded-full text-sm"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}

          {/* 完整內容 */}
          <div className="prose prose-lg max-w-none mb-8">
            <div className="text-gray-800 leading-relaxed whitespace-pre-line">
              {story.content}
            </div>
          </div>

          {/* 圖片展示區 */}
          {story.images && story.images.length > 0 && (
            <div className="mb-8">
              <h4 className="text-xl font-bold mb-4 text-gray-900">相關圖片</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {story.images.map((image, index) => (
                  <div key={index} className="rounded-lg overflow-hidden shadow-md">
                    <img
                      src={image}
                      alt={`${story.name} 相關圖片 ${index + 1}`}
                      className="w-full h-auto object-cover"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 影片展示區 */}
          {story.videos && story.videos.length > 0 && (
            <div className="mb-8">
              <h4 className="text-xl font-bold mb-4 text-gray-900">相關影片</h4>
              <div className="space-y-4">
                {story.videos.map((video, index) => (
                  <div key={index} className="rounded-lg overflow-hidden shadow-md">
                    <video
                      controls
                      className="w-full"
                      src={video}
                    >
                      您的瀏覽器不支援影片播放。
                    </video>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* YouTube 專訪影片區 */}
          {story.youtubeVideos && story.youtubeVideos.length > 0 && (
            <div className="mb-8">
              <h4 className="text-xl font-bold mb-4 text-gray-900 flex items-center gap-2">
                <svg 
                  className="w-6 h-6 text-red-600" 
                  fill="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                </svg>
                專訪影片
              </h4>
              <div className="space-y-6">
                {story.youtubeVideos.map((video, index) => (
                  <div key={index} className="rounded-lg overflow-hidden shadow-md bg-gray-50">
                    <div className="relative pb-[56.25%] h-0">
                      <iframe
                        className="absolute top-0 left-0 w-full h-full"
                        src={`https://www.youtube.com/embed/${video.id}`}
                        title={video.title}
                        frameBorder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                      />
                    </div>
                    <div className="p-4">
                      <h5 className="font-semibold text-gray-900 mb-2">
                        {video.title}
                      </h5>
                      {video.description && (
                        <p className="text-sm text-gray-600">
                          {video.description}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 音訊展示區 */}
          {story.audioUrl && (
            <div className="mb-8">
              <h4 className="text-xl font-bold mb-4 text-gray-900">口述歷史</h4>
              <div className="p-4 bg-gray-50 rounded-lg">
                <audio controls className="w-full" src={story.audioUrl}>
                  您的瀏覽器不支援音訊播放。
                </audio>
              </div>
            </div>
          )}

          {/* 相關連結 */}
          {story.relatedLinks && story.relatedLinks.length > 0 && (
            <div className="mb-8">
              <h4 className="text-xl font-bold mb-4 text-gray-900">延伸閱讀</h4>
              <ul className="space-y-2">
                {story.relatedLinks.map((link, index) => (
                  <li key={index}>
                    <a
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-2"
                    >
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                        />
                      </svg>
                      {link.title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 分隔線 */}
          <div className="border-t border-gray-200 pt-6 mt-6">
            {/* 貢獻資料按鈕 */}
            <div className="mb-6">
              <button
                onClick={handleContribute}
                className="w-full bg-green-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center justify-center gap-2 shadow-md"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                為這個故事補充資料
              </button>
              <p className="text-sm text-gray-500 text-center mt-2">
                如果您有更多關於此事件的資料、照片或影音，歡迎與我們分享
              </p>
            </div>
            
            <p className="text-sm text-gray-500 text-center">
              這些故事提醒我們珍惜得來不易的民主自由
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
