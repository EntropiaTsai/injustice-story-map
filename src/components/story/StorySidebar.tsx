import type { StoryLocation } from '../../types';

// 移除「歷年辦理匪案彙編：」書名前綴與開頭「匪」字，支援多組織（「、」分隔）
function normalizeOrg(raw: string | null | undefined): string | null {
  if (!raw) return null;
  const parts = raw.split(/[、，,](?=歷年辦理匪案彙編)/);
  const cleaned = parts.map(p =>
    p.replace(/歷年辦理匪案彙編[：:]/g, '').replace(/^匪/, '')
  );
  const result = cleaned.join('、');
  return result === '暫無資料' || result === '不詳' ? null : result;
}

interface StorySidebarProps {
  story: StoryLocation | null;
  onClose: () => void;
  isOpen: boolean;
  onContribute?: (storyId: string) => void;
}

export default function StorySidebar({ story, onClose, isOpen, onContribute }: StorySidebarProps) {
  if (!isOpen || !story) return null;

  const handleContribute = () => {
    if (onContribute && story) {
      onContribute(story.id);
    }
  };

  return (
    <>
      {/* 背景遮罩 - 手機版 */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-[1001] md:hidden"
        onClick={onClose}
      />
      
      {/* 側邊欄 */}
      <div
        className={`
          fixed top-0 right-0 h-full w-full md:w-[480px] lg:w-[560px]
          bg-white shadow-2xl z-[1002]
          transform transition-transform duration-300 ease-in-out
          overflow-y-auto
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}
        `}
      >
        {/* 關閉按鈕 */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full bg-gray-800 hover:bg-gray-900 text-white transition-colors z-10 shadow-lg"
          aria-label="關閉"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        {/* 內容區 */}
        <div className="p-6 md:p-8">
          {/* NHRM 記錄 */}
          {story.source === 'nhrm' && story.nhrm && (() => {
            const n = story.nhrm;
            const j = n.judgment;
            const birthYear = n.birth_year ? `${n.birth_year}` : null;
            const deathYear = n.death_year ? `${n.death_year}` : null;
            const lifespan = birthYear && deathYear ? `${birthYear}–${deathYear}`
              : birthYear ? `${birthYear}–`
              : deathYear ? `–${deathYear}` : null;
            const judgmentYear = j?.year_roc ? `民國 ${j.year_roc} 年（${j.year_roc + 1911} 年）` : null;
            const locationHint: Record<string, string> = {
              twtjdb: '被捕前居住地',
              nhrm_city: '籍貫（縣市）',
              nhrm_intro: '傳記文字推測',
              native: '籍貫（省）',
            };

            return (
              <>
                {/* 標題區：照片 + 姓名 */}
                <div className="flex items-start gap-4 mb-6">
                  {n.image_url && (
                    <img
                      src={n.image_url}
                      alt={story.name}
                      className="w-24 h-24 object-cover rounded-lg shadow border border-gray-200 flex-shrink-0"
                    />
                  )}
                  <div>
                    <div className="mb-1">
                      <span className="px-3 py-1 bg-stone-100 text-stone-700 rounded-full text-sm font-medium">
                        {lifespan || story.year}
                      </span>
                    </div>
                    <h2 className="text-3xl font-bold text-gray-900">{story.name}</h2>
                    {n.nickname && <p className="text-sm text-gray-500 mt-0.5">又名 {n.nickname}</p>}
                  </div>
                </div>

                {/* 案件 */}
                {n.cases.length > 0 && (
                  <div className="mb-4 flex flex-wrap gap-2">
                    {n.cases.map(c => (
                      <span key={c.id} className="px-3 py-1 bg-red-50 text-red-800 border border-red-200 rounded-full text-sm">
                        {c.name}
                      </span>
                    ))}
                  </div>
                )}

                {/* 傳記 */}
                {n.introduction && (
                  <div className="mb-6 text-gray-800 leading-relaxed text-[0.95rem] whitespace-pre-line">
                    {n.introduction}
                  </div>
                )}

                {/* 基本資料 */}
                <div className="mb-6 rounded-lg border border-gray-200 overflow-hidden">
                  <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                    <span className="text-sm font-semibold text-gray-600">基本資料</span>
                  </div>
                  <table className="w-full text-sm">
                    <tbody>
                      {[
                        ['性別', n.gender],
                        ['生年', birthYear],
                        ['卒年', deathYear],
                        ['籍貫', [n.province, n.city].filter(Boolean).join(' ')],
                        ['相關地點', n.place],
                        ['定位依據', n.location_source ? locationHint[n.location_source] : null],
                      ].filter(([, v]) => v).map(([label, value]) => (
                        <tr key={label as string} className="border-b border-gray-100 last:border-0">
                          <td className="px-4 py-2 text-gray-500 w-28">{label}</td>
                          <td className="px-4 py-2 text-gray-800">{value}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* 判決 */}
                {j && (
                  <div className="mb-6 rounded-lg border border-gray-200 overflow-hidden">
                    <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                      <span className="text-sm font-semibold text-gray-600">終審判決</span>
                    </div>
                    <table className="w-full text-sm">
                      <tbody>
                        {[
                          ['裁判機關', j.authority],
                          ['裁判年度', judgmentYear],
                          ['刑罰', j.penalty_text],
                          ['組織', normalizeOrg(j.organization)],
                          ['死刑', j.has_death_penalty ? '是' : null],
                          ['無期徒刑', j.has_life_sentence ? '是' : null],
                        ].filter(([, v]) => v).map(([label, value]) => (
                          <tr key={label as string} className="border-b border-gray-100 last:border-0">
                            <td className="px-4 py-2 text-gray-500 w-28">{label}</td>
                            <td className={`px-4 py-2 ${label === '死刑' || label === '無期徒刑' ? 'text-red-700 font-semibold' : 'text-gray-800'}`}>
                              {value}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* 平復補償 */}
                {n.recoup.length > 0 && (
                  <div className="mb-6">
                    <h4 className="text-sm font-semibold text-gray-600 mb-2">平復補償</h4>
                    <ul className="space-y-1">
                      {n.recoup.map((r, i) => (
                        <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                          <span className="text-green-600 mt-0.5 flex-shrink-0">✓</span>
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 同案相關人物（依 nhrm_id 去重） */}
                {n.related_persons.length > 0 && (() => {
                  const seen = new Set<number>();
                  const unique = n.related_persons.filter(p => {
                    if (seen.has(p.nhrm_id)) return false;
                    seen.add(p.nhrm_id);
                    return true;
                  });
                  return (
                    <div className="mb-6">
                      <h4 className="text-sm font-semibold text-gray-600 mb-2">同案相關人物</h4>
                      <div className="flex flex-wrap gap-2">
                        {unique.map(p => (
                          <span key={p.nhrm_id} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm">
                            {p.name}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })()}

                {/* 歷史文件 */}
                {n.documents.length > 0 && (
                  <div className="mb-6">
                    <h4 className="text-sm font-semibold text-gray-600 mb-2">相關歷史文件（{n.documents.length} 份）</h4>
                    <ul className="space-y-2">
                      {n.documents.map((d, i) => (
                        <li key={i} className="text-sm">
                          {d.image_url ? (
                            <a href={d.image_url} target="_blank" rel="noopener noreferrer"
                              className="text-blue-600 hover:underline flex items-start gap-1">
                              <span className="mt-0.5 flex-shrink-0">↗</span>
                              <span>{d.title || '文件'}{d.date ? `（${d.date}）` : ''}</span>
                            </a>
                          ) : (
                            <span className="text-gray-700">{d.title}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 連結 */}
                {n.nhrm_url && (
                  <a href={n.nhrm_url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-2 text-blue-600 hover:text-blue-800 hover:underline text-sm mb-6">
                    <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    國家人權記憶庫頁面
                  </a>
                )}

                <div className="border-t border-gray-200 pt-6">
                  <button onClick={handleContribute}
                    className="w-full bg-green-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center justify-center gap-2 shadow-md">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    為這個故事補充資料
                  </button>
                  <p className="text-sm text-gray-500 text-center mt-2">如果您知道更多關於此人的故事，歡迎與我們分享</p>
                </div>
              </>
            );
          })()}

          {/* twtjdb 自動匯入：精簡資料卡 */}
          {story.source === 'twtjdb' && story.twtjdb && (() => {
            const t = story.twtjdb;
            // birth_year_roc 實際儲存西元年（來自 Excel birth_h 欄位）
            const birthWestern = t.birth_year_roc ?? null;
            const birthRoc = birthWestern ? birthWestern - 1911 : null;
            const judgmentWestern = t.judgment_year_roc ? t.judgment_year_roc + 1911 : null;
            return (
              <>
                <div className="mb-4">
                  <span className="px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-sm font-medium">
                    {story.year}
                  </span>
                </div>
                <h2 className="text-3xl font-bold mb-1 text-gray-900">{story.name}</h2>
                <p className="text-sm text-amber-700 mb-6 flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  來自臺灣轉型正義資料庫，故事內容待補充
                </p>

                <div className="mb-6 rounded-lg border border-gray-200 overflow-hidden">
                  <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                    <span className="text-sm font-semibold text-gray-600">基本資料</span>
                  </div>
                  <table className="w-full text-sm">
                    <tbody>
                      {[
                        ['性別', t.gender],
                        ['出生年', birthRoc ? `民國${birthRoc}年（${birthWestern}年）` : null],
                        ['職業', t.occupation],
                        ['居住地（被捕前）', t.location_raw],
                      ].filter(([, v]) => v).map(([label, value]) => (
                        <tr key={label} className="border-b border-gray-100 last:border-0">
                          <td className="px-4 py-2 text-gray-500 w-36">{label}</td>
                          <td className="px-4 py-2 text-gray-800">{value}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mb-6 rounded-lg border border-gray-200 overflow-hidden">
                  <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                    <span className="text-sm font-semibold text-gray-600">終審判決</span>
                  </div>
                  <table className="w-full text-sm">
                    <tbody>
                      {[
                        ['裁判機關', t.judgment_authority],
                        ['裁判年度', judgmentWestern ? `民國${t.judgment_year_roc}年（${judgmentWestern}年）` : null],
                        ['刑罰', t.penalty_text],
                        ['組織', normalizeOrg(t.organization)],
                        ['死刑', t.has_death_penalty ? '是' : null],
                        ['無期徒刑', t.has_life_sentence ? '是' : null],
                      ].filter(([, v]) => v).map(([label, value]) => (
                        <tr key={label} className="border-b border-gray-100 last:border-0">
                          <td className="px-4 py-2 text-gray-500 w-36">{label}</td>
                          <td className={`px-4 py-2 ${label === '死刑' || label === '無期徒刑' ? 'text-red-700 font-semibold' : 'text-gray-800'}`}>{value}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <a
                  href="https://twtjdb.nhrm.gov.tw/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-blue-600 hover:text-blue-800 hover:underline text-sm mb-8"
                >
                  <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  臺灣轉型正義資料庫
                </a>

                <div className="border-t border-gray-200 pt-6">
                  <button
                    onClick={handleContribute}
                    className="w-full bg-green-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center justify-center gap-2 shadow-md"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    為這個故事補充資料
                  </button>
                  <p className="text-sm text-gray-500 text-center mt-2">
                    如果您知道更多關於此人的故事，歡迎與我們分享
                  </p>
                </div>
              </>
            );
          })()}

          {/* 一般手工策展故事 */}
          {story.source !== 'twtjdb' && <>
          {/* 標題區 */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                {story.year}
              </span>
            </div>
            <h2 className="text-3xl font-bold mb-2 text-gray-900">
              {story.title}
            </h2>
            <h3 className="text-xl text-gray-600 mb-2">
              {story.name}
            </h3>
            <p className="text-lg text-gray-700 font-medium">
              受難者：{story.victimName}
            </p>
          </div>

          {/* 摘要 */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg border-l-4 border-blue-500">
            <p className="text-gray-700 leading-relaxed">
              {story.summary}
            </p>
          </div>

          {/* 標籤 */}
          {story.tags && story.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-6">
              {story.tags.map((tag, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-gray-200 text-gray-700 rounded-full text-sm"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}

          {/* 完整內容 */}
          <div className="prose prose-lg max-w-none mb-8">
            <div className="text-gray-800 leading-relaxed whitespace-pre-line">
              {story.content}
            </div>
          </div>

          {/* 延伸閱讀：有補充敘事時使用醒目區塊，並可併列相關連結 */}
          {story.extendedReading?.trim() && (
            <div className="mb-8 rounded-xl border border-amber-200 bg-amber-50/80 p-5">
              <h4 className="text-lg font-bold text-amber-900 mb-3">
                延伸閱讀
              </h4>
              <div className="text-gray-800 leading-relaxed whitespace-pre-line text-[0.95rem] mb-4">
                {story.extendedReading}
              </div>
              {story.relatedLinks && story.relatedLinks.length > 0 && (
                <>
                  <p className="text-sm font-medium text-amber-900/90 mb-2">相關連結</p>
                  <ul className="space-y-2">
                    {story.relatedLinks.map((link, index) => (
                      <li key={index}>
                        <a
                          href={link.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-amber-800 hover:text-amber-950 hover:underline flex items-center gap-2 text-sm"
                        >
                          <svg
                            className="w-4 h-4 shrink-0"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                            />
                          </svg>
                          {link.title}
                        </a>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )}

          {/* 圖片展示區 */}
          {story.images && story.images.length > 0 && (
            <div className="mb-8">
              <h4 className="text-xl font-bold mb-4 text-gray-900">相關圖片</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {story.images.map((image, index) => (
                  <div key={index} className="rounded-lg overflow-hidden shadow-md">
                    <img
                      src={image}
                      alt={`${story.name} 相關圖片 ${index + 1}`}
                      className="w-full h-auto object-cover"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 影片展示區 */}
          {story.videos && story.videos.length > 0 && (
            <div className="mb-8">
              <h4 className="text-xl font-bold mb-4 text-gray-900">相關影片</h4>
              <div className="space-y-4">
                {story.videos.map((video, index) => (
                  <div key={index} className="rounded-lg overflow-hidden shadow-md">
                    <video
                      controls
                      className="w-full"
                      src={video}
                    >
                      您的瀏覽器不支援影片播放。
                    </video>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* YouTube 專訪影片區 */}
          {story.youtubeVideos && story.youtubeVideos.length > 0 && (
            <div className="mb-8">
              <h4 className="text-xl font-bold mb-4 text-gray-900 flex items-center gap-2">
                <svg 
                  className="w-6 h-6 text-red-600" 
                  fill="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                </svg>
                專訪影片
              </h4>
              <div className="space-y-6">
                {story.youtubeVideos.map((video, index) => (
                  <div key={index} className="rounded-lg overflow-hidden shadow-md bg-gray-50">
                    <div className="relative pb-[56.25%] h-0">
                      <iframe
                        className="absolute top-0 left-0 w-full h-full"
                        src={`https://www.youtube.com/embed/${video.id}`}
                        title={video.title}
                        frameBorder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                      />
                    </div>
                    <div className="p-4">
                      <h5 className="font-semibold text-gray-900 mb-2">
                        {video.title}
                      </h5>
                      {video.description && (
                        <p className="text-sm text-gray-600">
                          {video.description}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 音訊展示區 */}
          {story.audioUrl && (
            <div className="mb-8">
              <h4 className="text-xl font-bold mb-4 text-gray-900">口述歷史</h4>
              <div className="p-4 bg-gray-50 rounded-lg">
                <audio controls className="w-full" src={story.audioUrl}>
                  您的瀏覽器不支援音訊播放。
                </audio>
              </div>
            </div>
          )}

          {/* 相關連結（無 extendedReading 時維持原有藍色列表） */}
          {story.relatedLinks &&
            story.relatedLinks.length > 0 &&
            !story.extendedReading?.trim() && (
            <div className="mb-8">
              <h4 className="text-xl font-bold mb-4 text-gray-900">延伸閱讀</h4>
              <ul className="space-y-2">
                {story.relatedLinks.map((link, index) => (
                  <li key={index}>
                    <a
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-2"
                    >
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                        />
                      </svg>
                      {link.title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 分隔線 */}
          <div className="border-t border-gray-200 pt-6 mt-6">
            {/* 貢獻資料按鈕 */}
            <div className="mb-6">
              <button
                onClick={handleContribute}
                className="w-full bg-green-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center justify-center gap-2 shadow-md"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                為這個故事補充資料
              </button>
              <p className="text-sm text-gray-500 text-center mt-2">
                如果您有更多關於此事件的資料、照片或影音，歡迎與我們分享
              </p>
            </div>
            
            <p className="text-sm text-gray-500 text-center">
              這些故事提醒我們珍惜得來不易的民主自由
            </p>
          </div>
          </>}
        </div>
      </div>
    </>
  );
}
