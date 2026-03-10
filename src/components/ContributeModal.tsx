import { useState, useEffect } from 'react';
import { storyData } from '../data/stories';

interface ContributeModalProps {
  isOpen: boolean;
  onClose: () => void;
  storyId?: string | null;
}

export default function ContributeModal({ isOpen, onClose, storyId }: ContributeModalProps) {
  const [formData, setFormData] = useState({
    storyId: '',
    storyName: '',
    victimName: '',
    location: '',
    year: '',
    articleLinks: '',
    videoLinks: '',
    additionalInfo: '',
    submitterEmail: '',
  });

  // 當 storyId 變化時，自動填入相關資訊
  useEffect(() => {
    if (storyId) {
      const story = storyData.find(s => s.id === storyId);
      if (story) {
        setFormData(prev => ({
          ...prev,
          storyId: story.id,
          storyName: story.name,
          victimName: story.victimName,
          location: story.name,
          year: story.year,
        }));
      }
    } else {
      // 重置為新增故事模式
      setFormData(prev => ({
        ...prev,
        storyId: '',
        storyName: '',
        victimName: '',
        location: '',
        year: '',
      }));
    }
  }, [storyId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // 呼叫 API 提交資料
      const response = await fetch('/api/contribute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        // 顯示成功訊息
        if (storyId) {
          alert('感謝您為這個故事補充資料！我們會審核並更新內容。\n\n您的投稿編號：' + result.id);
        } else {
          alert('感謝您的貢獻！我們會審核並處理您提供的資料。\n\n您的投稿編號：' + result.id);
        }
        
        // 重置表單
        setFormData({
          storyId: '',
          storyName: '',
          victimName: '',
          location: '',
          year: '',
          articleLinks: '',
          videoLinks: '',
          additionalInfo: '',
          submitterEmail: '',
        });
        
        onClose();
      } else {
        alert('提交失敗：' + (result.error || '未知錯誤'));
      }
    } catch (error) {
      console.error('提交錯誤:', error);
      alert('提交時發生錯誤，請稍後再試');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-[2000] flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {storyId ? '為故事補充資料' : '貢獻故事素材'}
            </h2>
            {storyId && formData.storyName && (
              <p className="text-sm text-gray-600 mt-1">
                正在為「{formData.storyName}」補充資料
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full bg-gray-800 text-white hover:bg-gray-900 transition-colors"
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
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              📝 請提供您知道的受難者故事相關資料。我們會使用 AI 協助整理並驗證資料來源後，新增到地圖上。
            </p>
          </div>

          {/* 受難者姓名 */}
          <div>
            <label htmlFor="victimName" className="block text-sm font-medium text-gray-700 mb-2">
              受難者姓名 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="victimName"
              required
              value={formData.victimName}
              onChange={(e) => setFormData({ ...formData, victimName: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="例：蕭朝金"
            />
          </div>

          {/* 地點 */}
          <div>
            <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
              事件地點
            </label>
            <input
              type="text"
              id="location"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="例：高雄市岡山區"
            />
          </div>

          {/* 年份 */}
          <div>
            <label htmlFor="year" className="block text-sm font-medium text-gray-700 mb-2">
              事件年份
            </label>
            <input
              type="text"
              id="year"
              value={formData.year}
              onChange={(e) => setFormData({ ...formData, year: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="例：1947"
            />
          </div>

          {/* 文章連結 */}
          <div>
            <label htmlFor="articleLinks" className="block text-sm font-medium text-gray-700 mb-2">
              相關文章連結 <span className="text-red-500">*</span>
            </label>
            <textarea
              id="articleLinks"
              required
              rows={4}
              value={formData.articleLinks}
              onChange={(e) => setFormData({ ...formData, articleLinks: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="請提供相關文章連結（每行一個）&#10;例如：&#10;https://memory.nhrm.gov.tw/...&#10;https://www.228.org.tw/...&#10;https://storystudio.tw/..."
            />
            <p className="mt-1 text-xs text-gray-500">
              請提供官方資料庫、新聞報導、學術文章等可信來源
            </p>
          </div>

          {/* 影片連結 */}
          <div>
            <label htmlFor="videoLinks" className="block text-sm font-medium text-gray-700 mb-2">
              相關影片連結
            </label>
            <textarea
              id="videoLinks"
              rows={3}
              value={formData.videoLinks}
              onChange={(e) => setFormData({ ...formData, videoLinks: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="YouTube 影片連結（每行一個）&#10;例如：&#10;https://youtu.be/..."
            />
          </div>

          {/* 補充資訊 */}
          <div>
            <label htmlFor="additionalInfo" className="block text-sm font-medium text-gray-700 mb-2">
              補充資訊
            </label>
            <textarea
              id="additionalInfo"
              rows={4}
              value={formData.additionalInfo}
              onChange={(e) => setFormData({ ...formData, additionalInfo: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="其他您想分享的資訊，例如：&#10;- 您與受難者的關係&#10;- 家族口述歷史&#10;- 其他重要細節"
            />
          </div>

          {/* 聯絡信箱（選填） */}
          <div>
            <label htmlFor="submitterEmail" className="block text-sm font-medium text-gray-700 mb-2">
              您的聯絡信箱（選填）
            </label>
            <input
              type="email"
              id="submitterEmail"
              value={formData.submitterEmail}
              onChange={(e) => setFormData({ ...formData, submitterEmail: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="如果我們需要進一步確認資料，可以聯絡您"
            />
          </div>

          {/* 提交按鈕 */}
          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              提交資料
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-3 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-xs text-yellow-800">
              ⚠️ 重要提醒：
              <br />
              1. 請確保提供的資料來源可靠且可公開查證
              <br />
              2. 我們會使用 AI 協助整理資料，但仍需人工審核
              <br />
              3. 審核通過後才會新增到地圖上
              <br />
              4. 提交的資料可能需要數日至數週處理
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
