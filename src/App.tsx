import { useState, useMemo } from 'react';
import MapView from './components/map/MapView';
import StorySidebar from './components/story/StorySidebar';
import Header from './components/layout/Header';
import AboutModal from './components/layout/AboutModal';
import ContributeModal from './components/ContributeModal';
import { storyData } from './data/stories';
import { useTwtjdbData } from './hooks/useTwtjdbData';
import type { StoryLocation } from './types';

function App() {
  const { data: twtjdbStories } = useTwtjdbData();
  const allStories = useMemo(() => {
    // 若 twtjdb 記錄與手工標記距離太近，整組推離，避免群集泡泡蓋住精確地點
    const THRESHOLD = 0.20; // ~22km：判定「太近」的範圍
    const PUSH = 0.04;      // ~4km：視覺上錯開即可
    const adjusted = twtjdbStories.map(story => {
      const near = storyData.find(
        c => Math.hypot(c.lat - story.lat, c.lng - story.lng) < THRESHOLD
      );
      if (!near) return story;
      const dlat = story.lat - near.lat;
      const dlng = story.lng - near.lng;
      const dist = Math.hypot(dlat, dlng) || 0.001;
      return { ...story, lat: story.lat + (dlat / dist) * PUSH, lng: story.lng + (dlng / dist) * PUSH };
    });
    return [...storyData, ...adjusted];
  }, [twtjdbStories]);

  const [selectedStory, setSelectedStory] = useState<StoryLocation | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isAboutModalOpen, setIsAboutModalOpen] = useState(false);
  const [isContributeModalOpen, setIsContributeModalOpen] = useState(false);
  const [contributeForStoryId, setContributeForStoryId] = useState<string | null>(null);

  const handleStorySelect = (story: StoryLocation) => {
    setSelectedStory(story);
    setIsSidebarOpen(true);
  };

  const handleCloseSidebar = () => {
    setIsSidebarOpen(false);
    // 延遲清除選中狀態，讓關閉動畫完成
    setTimeout(() => {
      setSelectedStory(null);
    }, 300);
  };

  const handleContributeForStory = (storyId: string) => {
    setContributeForStoryId(storyId);
    setIsContributeModalOpen(true);
  };

  const handleCloseContributeModal = () => {
    setIsContributeModalOpen(false);
    setContributeForStoryId(null);
  };

  return (
    <div className="w-full h-screen flex flex-col">
      <Header 
        onAboutClick={() => setIsAboutModalOpen(true)}
        onContributeClick={() => setIsContributeModalOpen(true)}
      />
      
      <main className="flex-1 pt-[72px] relative">
        <MapView
          stories={allStories}
          onStorySelect={handleStorySelect}
          selectedStoryId={selectedStory?.id || null}
        />
        
        <StorySidebar
          story={selectedStory}
          onClose={handleCloseSidebar}
          isOpen={isSidebarOpen}
          onContribute={handleContributeForStory}
        />
      </main>

      <AboutModal
        isOpen={isAboutModalOpen}
        onClose={() => setIsAboutModalOpen(false)}
      />

      <ContributeModal
        isOpen={isContributeModalOpen}
        onClose={handleCloseContributeModal}
        storyId={contributeForStoryId}
      />

      {/* 首次訪問提示 */}
      {!selectedStory && (
        <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-[999] pointer-events-none">
          <div className="bg-gray-800 text-white rounded-lg shadow-lg px-6 py-3 pointer-events-auto">
            <p className="text-sm font-medium">
              👆 點擊地圖上的藍色標記查看故事
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
