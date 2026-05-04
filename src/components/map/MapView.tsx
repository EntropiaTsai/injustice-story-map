import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'react-leaflet-cluster/lib/assets/MarkerCluster.css';
import 'react-leaflet-cluster/lib/assets/MarkerCluster.Default.css';
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

// 群集圖標：大小依數量分三級，配合地圖深色風格
const createClusterIcon = (cluster: { getChildCount: () => number }) => {
  const count = cluster.getChildCount();
  const size = count > 50 ? 52 : count > 10 ? 44 : 36;
  const fontSize = count > 99 ? 11 : 13;
  return L.divIcon({
    className: 'custom-cluster-icon',
    html: `<div style="
      background: rgba(30,41,59,0.88);
      border: 2.5px solid rgba(255,255,255,0.85);
      border-radius: 50%;
      width: ${size}px;
      height: ${size}px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: 700;
      font-size: ${fontSize}px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.45);
      font-family: sans-serif;
    ">${count}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};

type PenaltyLevel = 'death' | 'heavy' | 'light' | 'unknown';

const PENALTY_COLOR: Record<PenaltyLevel, string> = {
  death:   '#dc2626', // 紅
  heavy:   '#d97706', // 橘
  light:   '#3b82f6', // 藍
  unknown: '#6b7280', // 灰
};

// 依刑罰等級決定顏色；curated 故事較大且有箭頭，twtjdb 較小純圓點
// 選中時加白色外環以區別
const createCustomIcon = (
  isSelected: boolean,
  penaltyLevel: PenaltyLevel = 'unknown',
  isCurated: boolean = false
) => {
  const color = PENALTY_COLOR[penaltyLevel];
  const selectedRing = isSelected
    ? `outline:3px solid white;outline-offset:2px;`
    : '';

  if (isCurated) {
    return L.divIcon({
      className: 'custom-marker',
      html: `<div style="background-color:${color};width:30px;height:30px;border-radius:50%;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;cursor:pointer;${selectedRing}">
        <svg width="16" height="16" fill="white" viewBox="0 0 16 16"><path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0zM4.5 7.5a.5.5 0 0 0 0 1h5.793l-2.147 2.146a.5.5 0 0 0 .708.708l3-3a.5.5 0 0 0 0-.708l-3-3a.5.5 0 1 0-.708.708L10.293 7.5H4.5z"/></svg>
      </div>`,
      iconSize: [30, 30],
      iconAnchor: [15, 15],
      popupAnchor: [0, -15],
    });
  }

  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="background-color:${color};width:20px;height:20px;border-radius:50%;border:2px solid white;box-shadow:0 1px 5px rgba(0,0,0,0.3);cursor:pointer;opacity:0.85;${selectedRing}"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
    popupAnchor: [0, -10],
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

  // 台澎金馬的地理邊界
  const taiwanBounds: L.LatLngBoundsExpression = [
    [21.8, 117.5],  // 西南角：117.5°E 涵蓋金門（118.3°E）
    [26.5, 122.1]   // 東北角：26.5°N 涵蓋馬祖（26.1°N）
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
        
        {/* 手工策展故事：精確地點，永遠以個別標記顯示，不進群集 */}
        {stories.filter(s => s.source !== 'twtjdb').map((story) => (
          <Marker
            key={story.id}
            position={[story.lat, story.lng]}
            icon={createCustomIcon(story.id === selectedStoryId, story.penaltyLevel as PenaltyLevel, true)}
            zIndexOffset={1000}
            eventHandlers={{ click: () => onStorySelect(story) }}
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

        {/* 資料庫紀錄：縣市層級座標加隨機偏移，群集顯示 */}
        <MarkerClusterGroup
          iconCreateFunction={createClusterIcon}
          maxClusterRadius={60}
          spiderfyOnMaxZoom={true}
          showCoverageOnHover={false}
          chunkedLoading
        >
          {stories.filter(s => s.source === 'twtjdb').map((story) => (
            <Marker
              key={story.id}
              position={[story.lat, story.lng]}
              icon={createCustomIcon(story.id === selectedStoryId, story.penaltyLevel as PenaltyLevel, false)}
              eventHandlers={{ click: () => onStorySelect(story) }}
            >
              <Popup>
                <div className="p-2">
                  <h3 className="font-bold text-base mb-1">{story.victimName}</h3>
                  <p className="text-xs text-gray-500 mb-1">{story.twtjdb?.location_raw} · {story.year}</p>
                  <p className="text-sm mb-2">{story.summary}</p>
                  <button
                    onClick={() => onStorySelect(story)}
                    className="text-amber-700 hover:text-amber-900 text-sm font-medium"
                  >
                    查看資料 →
                  </button>
                </div>
              </Popup>
            </Marker>
          ))}
        </MarkerClusterGroup>

        <MapController selectedStory={selectedStory || null} />
      </MapContainer>

      {/* 地圖圖例 */}
      <div className="absolute bottom-6 left-6 bg-white rounded-lg shadow-lg p-4 z-[1000]">
        <h4 className="font-bold text-sm mb-2 text-gray-900">圖例</h4>
        <div className="flex items-center gap-2 text-sm">
          <div className="w-3 h-3 rounded-full flex-shrink-0" style={{backgroundColor:'#dc2626'}}></div>
          <span className="text-gray-700">死刑／槍決</span>
        </div>
        <div className="flex items-center gap-2 text-sm mt-1">
          <div className="w-3 h-3 rounded-full flex-shrink-0" style={{backgroundColor:'#d97706'}}></div>
          <span className="text-gray-700">有期徒刑 10 年以上</span>
        </div>
        <div className="flex items-center gap-2 text-sm mt-1">
          <div className="w-3 h-3 rounded-full flex-shrink-0" style={{backgroundColor:'#3b82f6'}}></div>
          <span className="text-gray-700">有期徒刑 10 年以下</span>
        </div>
        <div className="flex items-center gap-2 text-sm mt-1">
          <div className="w-3 h-3 rounded-full flex-shrink-0" style={{backgroundColor:'#6b7280'}}></div>
          <span className="text-gray-700">其他</span>
        </div>
        <div className="border-t border-gray-200 mt-2 pt-2 flex items-center gap-2 text-sm">
          
          <span className="text-gray-500 text-xs">● 基本紀錄（僅知人物與地點）</span>
          <span className="text-gray-500 text-xs">➝ 完整事件（含歷史敘述）</span>
        </div>
      </div>
    </div>
  );
}
