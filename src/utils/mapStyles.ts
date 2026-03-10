// 地圖樣式配置
export const mapStyles = {
  // 懷舊風格 - 牛皮紙質感 + 中文地名
  vintage: {
    name: '懷舊風格',
    url: 'https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}&hl=zh-TW',
    attribution: '&copy; Google Maps',
    filter: 'sepia(60%) brightness(95%) contrast(95%) saturate(80%) hue-rotate(-10deg)',
  },
};

export type MapStyleKey = keyof typeof mapStyles;
