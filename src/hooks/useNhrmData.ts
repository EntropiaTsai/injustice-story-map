import { useState, useEffect } from 'react';
import type { StoryLocation, NhrmMeta } from '../types';

interface NhrmPerson {
  nhrm_id: number;
  twtjdb_id: string | null;
  name: string;
  nickname: string | null;
  gender: string | null;
  birth_year: string | null;
  death_year: string | null;
  province: string | null;
  city: string | null;
  place: string | null;
  lat: number;
  lng: number;
  location_source: 'twtjdb' | 'nhrm_city' | 'nhrm_place' | 'nhrm_intro' | 'native' | 'llm';
  location_raw: string | null;
  penalty_level: 'death' | 'heavy' | 'light' | 'unknown';
  image_url: string | null;
  summary: string | null;
  introduction: string | null;
  nhrm_url: string | null;
  judgment: NhrmMeta['judgment'];
  cases: NhrmMeta['cases'];
  related_persons: NhrmMeta['related_persons'];
  recoup: string[];
  documents: NhrmMeta['documents'];
}

function toStoryLocation(p: NhrmPerson): StoryLocation {
  const j = p.judgment;
  const yearLabel = p.death_year
    ? `${p.death_year} 年`
    : j?.year_roc
    ? `民國 ${j.year_roc} 年`
    : '年代不詳';

  const summary = p.summary
    || (p.introduction
      ? p.introduction.slice(0, 120).replace(/\n/g, ' ') + (p.introduction.length > 120 ? '…' : '')
      : j?.penalty_text || '資料待補');

  const nhrm: NhrmMeta = {
    nhrm_id: p.nhrm_id,
    twtjdb_id: p.twtjdb_id,
    nickname: p.nickname,
    gender: p.gender,
    birth_year: p.birth_year,
    death_year: p.death_year,
    province: p.province,
    city: p.city,
    place: p.place,
    location_source: p.location_source,
    image_url: p.image_url,
    summary: p.summary ?? null,
    introduction: p.introduction,
    nhrm_url: p.nhrm_url,
    judgment: p.judgment,
    cases: p.cases,
    related_persons: p.related_persons,
    recoup: p.recoup,
    documents: p.documents,
  };

  return {
    id: `nhrm-${p.nhrm_id}`,
    name: p.name,
    victimName: p.name,
    penaltyLevel: p.penalty_level,
    lat: p.lat,
    lng: p.lng,
    year: yearLabel,
    title: p.name,
    summary,
    content: p.introduction || '',
    source: 'nhrm',
    nhrm,
  };
}

export function useNhrmData() {
  const [data, setData] = useState<StoryLocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetch('/data/nhrm_map_ready.json')
      .then(r => r.json())
      .then((json: { persons: NhrmPerson[] }) => {
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
