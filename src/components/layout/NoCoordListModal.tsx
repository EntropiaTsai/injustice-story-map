import { useState, useEffect, useMemo } from 'react';

interface NoCoordRecord {
  nhrm_id: number;
  name: string;
  nickname: string | null;
  gender: string | null;
  birth_year: string | null;
  death_year: string | null;
  province: string | null;
  city: string | null;
  place: string | null;
  penalty_level: string;
  penalty_text: string | null;
  year_roc: number | null;
  introduction: string | null;
  nhrm_url: string | null;
  cases: { id: number | null; name: string | null }[];
}

interface NoCoordListModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const PENALTY_LABEL: Record<string, string> = {
  death: '死刑',
  heavy: '重刑',
  light: '輕刑',
  unknown: '不明',
};

const PENALTY_COLOR: Record<string, string> = {
  death: 'bg-red-100 text-red-800',
  heavy: 'bg-orange-100 text-orange-800',
  light: 'bg-yellow-100 text-yellow-800',
  unknown: 'bg-gray-100 text-gray-600',
};

export default function NoCoordListModal({ isOpen, onClose }: NoCoordListModalProps) {
  const [records, setRecords] = useState<NoCoordRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [penaltyFilter, setPenaltyFilter] = useState<string>('all');
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    if (!isOpen || records.length > 0) return;
    setLoading(true);
    fetch('/data/nhrm_no_coord.json')
      .then(r => r.json())
      .then((data: NoCoordRecord[]) => { setRecords(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [isOpen, records.length]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return records.filter(r => {
      if (penaltyFilter !== 'all' && r.penalty_level !== penaltyFilter) return false;
      if (!q) return true;
      return (
        r.name.includes(q) ||
        (r.nickname || '').toLowerCase().includes(q) ||
        (r.province || '').includes(q) ||
        (r.city || '').includes(q) ||
        (r.place || '').includes(q) ||
        (r.introduction || '').includes(q) ||
        r.cases.some(c => (c.name || '').includes(q))
      );
    });
  }, [records, query, penaltyFilter]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[2000] flex items-center justify-center p-2 md:p-4">
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose} />

      <div className="relative bg-white rounded-lg shadow-2xl w-full max-w-5xl max-h-[95vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 flex-shrink-0">
          <div>
            <h2 className="text-xl font-bold text-gray-900">待補座標人員清單</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              共 {records.length} 筆尚未有地理座標，目前篩選顯示 {filtered.length} 筆
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full bg-gray-800 hover:bg-gray-900 text-white transition-colors"
            aria-label="關閉"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3 px-6 py-3 border-b border-gray-100 flex-shrink-0">
          <input
            type="text"
            placeholder="搜尋姓名、地點、省份、案由..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <select
            value={penaltyFilter}
            onChange={e => setPenaltyFilter(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            <option value="all">所有刑罰</option>
            <option value="death">死刑</option>
            <option value="heavy">重刑</option>
            <option value="light">輕刑</option>
            <option value="unknown">不明</option>
          </select>
        </div>

        {/* List */}
        <div className="overflow-y-auto flex-1">
          {loading ? (
            <div className="flex items-center justify-center py-20 text-gray-500">載入中...</div>
          ) : filtered.length === 0 ? (
            <div className="flex items-center justify-center py-20 text-gray-400">無符合結果</div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 w-8">#</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">姓名</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 hidden sm:table-cell">省籍</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 hidden md:table-cell">城市</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 hidden lg:table-cell">關押地</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">刑罰</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 hidden md:table-cell">年份</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">查詢</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((r, idx) => (
                  <>
                    <tr
                      key={r.nhrm_id}
                      className="hover:bg-gray-50 cursor-pointer"
                      onClick={() => setExpandedId(expandedId === r.nhrm_id ? null : r.nhrm_id)}
                    >
                      <td className="px-4 py-2.5 text-gray-400 text-xs">{idx + 1}</td>
                      <td className="px-4 py-2.5">
                        <span className="font-medium text-gray-900">{r.name}</span>
                        {r.nickname && <span className="text-gray-400 text-xs ml-1">（{r.nickname}）</span>}
                        {r.introduction && (
                          <span className="ml-1 text-gray-300 text-xs">▸</span>
                        )}
                      </td>
                      <td className="px-4 py-2.5 text-gray-600 hidden sm:table-cell">
                        {r.province || '—'}
                      </td>
                      <td className="px-4 py-2.5 text-gray-600 hidden md:table-cell">
                        {r.city || '—'}
                      </td>
                      <td className="px-4 py-2.5 text-gray-600 hidden lg:table-cell max-w-[160px] truncate">
                        {r.place || '—'}
                      </td>
                      <td className="px-4 py-2.5">
                        <span className={`inline-block text-xs px-2 py-0.5 rounded-full font-medium ${PENALTY_COLOR[r.penalty_level] || PENALTY_COLOR.unknown}`}>
                          {PENALTY_LABEL[r.penalty_level] || '不明'}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-gray-600 hidden md:table-cell">
                        {r.year_roc ? `民國${r.year_roc}年` : '—'}
                      </td>
                      <td className="px-4 py-2.5">
                        {r.nhrm_url ? (
                          <a
                            href={r.nhrm_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={e => e.stopPropagation()}
                            className="text-blue-600 hover:text-blue-800 underline text-xs"
                          >
                            NHRM
                          </a>
                        ) : (
                          <span className="text-gray-300 text-xs">—</span>
                        )}
                      </td>
                    </tr>
                    {expandedId === r.nhrm_id && (
                      <tr key={`${r.nhrm_id}-detail`} className="bg-blue-50">
                        <td colSpan={8} className="px-6 py-3">
                          <div className="text-sm space-y-1.5 text-gray-700">
                            {r.place && (
                              <p><span className="font-medium text-gray-500">關押地：</span>{r.place}</p>
                            )}
                            {r.penalty_text && (
                              <p><span className="font-medium text-gray-500">刑罰：</span>{r.penalty_text}</p>
                            )}
                            {r.cases.length > 0 && (
                              <p><span className="font-medium text-gray-500">案件：</span>
                                {r.cases.map(c => c.name).filter(Boolean).join('、') || '—'}
                              </p>
                            )}
                            {r.introduction && (
                              <p className="text-gray-600 text-xs leading-relaxed border-t border-blue-100 pt-2 mt-2">
                                {r.introduction.slice(0, 300)}{r.introduction.length > 300 ? '…' : ''}
                              </p>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Footer hint */}
        <div className="px-6 py-3 border-t border-gray-100 bg-gray-50 text-xs text-gray-500 flex-shrink-0 rounded-b-lg">
          點擊任一列可展開簡介 · 若確認座標請使用 NHRM 連結確認後協助補充
        </div>
      </div>
    </div>
  );
}
