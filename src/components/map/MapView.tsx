import { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { StoryLocation } from '../../types';
import { mapStyles, type MapStyleKey } from '../../utils/mapStyles';

// 修復 Leaflet 預設圖標問題
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

// 自訂故事標記圖標
const createCustomIcon = (isSelected: boolean) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        background-color: ${isSelected ? '#dc2626' : '#3b82f6'};
        width: 30px;
        height: 30px;
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.3s ease;
      ">
        <svg width="16" height="16" fill="white" viewBox="0 0 16 16">
          <path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0zM4.5 7.5a.5.5 0 0 0 0 1h5.793l-2.147 2.146a.5.5 0 0 0 .708.708l3-3a.5.5 0 0 0 0-.708l-3-3a.5.5 0 1 0-.708.708L10.293 7.5H4.5z"/>
        </svg>
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15],
  });
};

interface MapViewProps {
  stories: StoryLocation[];
  onStorySelect: (story: StoryLocation) => void;
  selectedStoryId: string | null;
}

// 地圖控制組件 - 用於在選擇故事時移動地圖視圖
function MapController({ selectedStory }: { selectedStory: StoryLocation | null }) {
  const map = useMap();
  
  if (selectedStory) {
    map.flyTo([selectedStory.lat, selectedStory.lng], 13, {
      duration: 1.5
    });
  }
  
  return null;
}

export default function MapView({ stories, onStorySelect, selectedStoryId }: MapViewProps) {
  const currentMapStyle: MapStyleKey = 'vintage'; // 固定使用懷舊風格
  
  const taiwanCenter: [number, number] = [23.5, 121];
  const selectedStory = stories.find(s => s.id === selectedStoryId);
  const selectedStyle = mapStyles[currentMapStyle];

  // 台澎金馬的地理邊界（更嚴格的限制）
  const taiwanBounds: L.LatLngBoundsExpression = [
    [21.8, 119.3],  // 西南角（涵蓋東沙、南沙最南端）
    [25.3, 122.1]   // 東北角（涵蓋馬祖最北端）
  ];

  return (
    <div className="w-full h-full relative">
      <MapContainer
        center={taiwanCenter}
        zoom={8}
        className="w-full h-full"
        zoomControl={true}
        maxBounds={taiwanBounds}
        maxBoundsViscosity={1.0}
        minZoom={7}
        maxZoom={18}
      >
        {/* 使用 Google Maps 圖層（含中文地名） */}
        <TileLayer
          key={currentMapStyle}
          attribution={selectedStyle.attribution}
          url={selectedStyle.url}
        />
        
        {/* 應用濾鏡效果 */}
        <style>{`
          .leaflet-tile-pane {
            filter: ${selectedStyle.filter};
          }
        `}</style>
        
        {stories.map((story) => (
          <Marker
            key={story.id}
            position={[story.lat, story.lng]}
            icon={createCustomIcon(story.id === selectedStoryId)}
            eventHandlers={{
              click: () => onStorySelect(story),
            }}
          >
            <Popup>
              <div className="p-2">
                <h3 className="font-bold text-lg mb-1">{story.name}</h3>
                <p className="text-sm text-gray-600 mb-2">{story.victimName}</p>
                <p className="text-sm mb-2">{story.summary}</p>
                <button
                  onClick={() => onStorySelect(story)}
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  查看完整故事 →
                </button>
              </div>
            </Popup>
          </Marker>
        ))}
        
        <MapController selectedStory={selectedStory || null} />
      </MapContainer>

      {/* 地圖圖例 */}
      <div className="absolute bottom-6 left-6 bg-white rounded-lg shadow-lg p-4 z-[1000]">
        <h4 className="font-bold text-sm mb-2 text-gray-900">圖例</h4>
        <div className="flex items-center gap-2 text-sm">
          <div className="w-4 h-4 rounded-full bg-blue-500 border-2 border-white"></div>
          <span className="text-gray-700">故事地點</span>
        </div>
        <div className="flex items-center gap-2 text-sm mt-2">
          <div className="w-4 h-4 rounded-full bg-red-600 border-2 border-white"></div>
          <span className="text-gray-700">已選擇</span>
        </div>
      </div>
    </div>
  );
}
