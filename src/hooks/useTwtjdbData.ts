import { useState, useEffect } from 'react';
import type { StoryLocation } from '../types';

interface TwtjdbPerson {
  id: string;
  name: string;
  gender: string;
  birth_year_roc: number | null;
  occupation: string | null;
  lat: number;
  lng: number;
  location_raw: string;
  judgment: {
    authority: string | null;
    year_roc: number | null;
    penalty_text: string | null;
    has_death_penalty: boolean;
    has_life_sentence: boolean;
    organization: string | null;
  };
}

// 根據 id 產生確定性偏移，讓同縣市的點散布在縣市範圍內而非全部疊在中心點
function jitter(id: string): [number, number] {
  let h = 0;
  for (const c of id) {
    h = (Math.imul(31, h) + c.charCodeAt(0)) | 0;
  }
  const lat = ((h & 0xffff) / 0xffff - 0.5) * 0.22;
  const lng = (((h >> 16) & 0xffff) / 0xffff - 0.5) * 0.28;
  return [lat, lng];
}

function toStoryLocation(p: TwtjdbPerson): StoryLocation {
  const year = p.judgment.year_roc ? String(p.judgment.year_roc + 1911) : '年代不詳';
  const tags = [p.location_raw, p.judgment.organization].filter(Boolean) as string[];
  const [jLat, jLng] = jitter(p.id);

  return {
    id: `twtjdb-${p.id}`,
    name: p.name,
    victimName: p.name,
    lat: p.lat + jLat,
    lng: p.lng + jLng,
    year,
    title: p.name,
    summary: p.judgment.penalty_text || '刑罰資料待補',
    content: '',
    tags,
    source: 'twtjdb',
    twtjdb: {
      gender: p.gender,
      birth_year_roc: p.birth_year_roc,
      occupation: p.occupation,
      location_raw: p.location_raw,
      judgment_authority: p.judgment.authority,
      judgment_year_roc: p.judgment.year_roc,
      penalty_text: p.judgment.penalty_text,
      has_death_penalty: p.judgment.has_death_penalty,
      has_life_sentence: p.judgment.has_life_sentence,
      organization: p.judgment.organization,
    },
  };
}

export function useTwtjdbData() {
  const [data, setData] = useState<StoryLocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetch('/data/twtjdb_map_ready.json')
      .then(r => r.json())
      .then((json: { persons: TwtjdbPerson[] }) => {
        setData(json.persons.map(toStoryLocation));
        setLoading(false);
      })
      .catch((err: Error) => {
        setError(err);
        setLoading(false);
      });
  }, []);

  return { data, loading, error };
}
