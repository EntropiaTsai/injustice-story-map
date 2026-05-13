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
  source?: 'twtjdb' | 'nhrm';
  twtjdb?: TwtjdbMeta;
  nhrm?: NhrmMeta;
  /** 刑罰等級：death 死刑/槍決、heavy 10年以上、light 10年以下、unknown 不明 */
  penaltyLevel?: 'death' | 'heavy' | 'light' | 'unknown';
}

export interface NhrmMeta {
  nhrm_id: number;
  twtjdb_id: string | null;
  nickname: string | null;
  gender: string | null;
  birth_year: string | null;
  death_year: string | null;
  province: string | null;
  city: string | null;
  place: string | null;
  location_source: 'twtjdb' | 'nhrm_city' | 'nhrm_place' | 'nhrm_intro' | 'native' | 'llm' | 'audit' | null;
  arrest_location: string | null;
  image_url: string | null;
  summary: string | null;
  introduction: string | null;
  nhrm_url: string | null;
  judgment: {
    authority: string | null;
    year_roc: number | null;
    penalty_text: string | null;
    has_death_penalty: boolean;
    has_life_sentence: boolean;
    organization: string | null;
  } | null;
  cases: { id: number; name: string }[];
  related_persons: { nhrm_id: number; name: string }[];
  recoup: string[];
  documents: {
    doc_id: number | null;
    title: string | null;
    authority: string | null;
    related_persons: string | null;
    date: string | null;
    image_url: string | null;
  }[];
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
