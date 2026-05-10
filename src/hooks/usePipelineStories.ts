import { useState, useEffect } from 'react';
import type { StoryLocation } from '../types';

export function usePipelineStories() {
  const [data, setData] = useState<StoryLocation[]>([]);

  useEffect(() => {
    fetch('/data/pipeline_stories.json')
      .then(r => r.json())
      .then((stories: StoryLocation[]) => {
        // 只取有座標的上地圖，其餘忽略
        setData(stories.filter(s => s.lat != null && s.lng != null));
      })
      .catch(() => {
        // 檔案不存在時靜默略過
      });
  }, []);

  return data;
}
