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
  /** 主文以外的補充段落（例如同一人的其他案件），顯示於側欄「延伸閱讀」 */
  extendedReading?: string;
  tags?: string[];
  /** 資料來源：twtjdb 表示從轉型正義資料庫自動匯入，內容待補充 */
  source?: 'twtjdb';
  twtjdb?: TwtjdbMeta;
}

export interface TwtjdbMeta {
  gender: string | null;
  birth_year_roc: number | null;
  occupation: string | null;
  location_raw: string | null;
  judgment_authority: string | null;
  judgment_year_roc: number | null;
  penalty_text: string | null;
  has_death_penalty: boolean;
  has_life_sentence: boolean;
  organization: string | null;
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
