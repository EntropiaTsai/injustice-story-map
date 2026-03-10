export interface StoryLocation {
  id: string;
  name: string;
  victimName: string;
  lat: number;
  lng: number;
  year: string;
  title: string;
  summary: string;
  content: string;
  images?: string[];
  videos?: string[];
  youtubeVideos?: {
    id: string;           // YouTube 影片 ID
    title: string;        // 影片標題
    description?: string; // 影片說明
  }[];
  audioUrl?: string;
  relatedLinks?: {
    title: string;
    url: string;
  }[];
  tags?: string[];
}

export enum StoryCategory {
  Prison = 'prison',
  ExecutionGround = 'execution',
  Cemetery = 'cemetery',
  Court = 'court',
  Memorial = 'memorial',
  Historical = 'historical',
  Other = 'other',
}
