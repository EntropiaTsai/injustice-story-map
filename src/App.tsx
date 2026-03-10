import { useState } from 'react';
import MapView from './components/map/MapView';
import StorySidebar from './components/story/StorySidebar';
import Header from './components/layout/Header';
import AboutModal from './components/layout/AboutModal';
import ContributeModal from './components/ContributeModal';
import { storyData } from './data/stories';
import type { StoryLocation } from './types';

function App() {
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
          stories={storyData}
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
