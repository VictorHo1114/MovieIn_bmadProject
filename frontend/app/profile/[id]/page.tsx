import { API_BASE } from "../../../lib/config";
import type { UserPublic } from "../../../lib/types/user";
import Link from 'next/link';
import ProfileEditorClient from '../../../components/ProfileEditorClient';

export default async function OtherProfilePage({ params }: { params: { id: string } } | any) {
  const { id: userId } = await params;
  if (!userId) {
    return <div className="p-6">找不到該使用者。</div>;
  }

  try {
    // Try several candidate bases because backend may be mounted with or without /api or /api/v1
    const candidatesRaw = [API_BASE, 'http://127.0.0.1:8000', 'http://localhost:8000', 'http://127.0.0.1:8000/api', 'http://127.0.0.1:8000/api/v1', 'http://localhost:8000/api', 'http://localhost:8000/api/v1'];
    const candidates = Array.from(new Set(
      candidatesRaw.flatMap(b => [
        b,
        // variants: strip trailing /api or /api/v1
        b.replace(/\/api\/v1\/?$/,'').replace(/\/api\/?$/,''),
      ])
    ));
    const details: { url: string; status: number; text?: string }[] = [];
    let lastRes: Response | null = null;
    let user: UserPublic | null = null;

    for (const base of candidates) {
      const url = `${base}/profile/${userId}`;
      try {
        const res = await fetch(url, { cache: 'no-store' });
        lastRes = res;
        const text = await res.text().catch(() => '');
        details.push({ url, status: res.status, text: text.length > 200 ? text.slice(0, 200) + '...' : text });
        if (res.ok) {
          try {
            user = JSON.parse(text) as UserPublic;
          } catch (e) {
            // if parsing fails, try res.json()
            user = await res.json();
          }
          break;
        }
        // try next candidate if not ok
      } catch (err: any) {
        details.push({ url, status: 0, text: String(err.message ?? err) });
      }
    }

    if (user) {
      // Fetch public watchlist and top10 for this user (預設公開)
      let publicWatchlist: any[] = [];
      let publicTop10: any[] = [];

      for (const base of candidates) {
        try {
          const root = base.replace(/\/$/, '');
          const wurl = `${root}/watchlist/public/${userId}`;
          const twurl = `${root}/top10/public/${userId}`;

          const [wr, tr] = await Promise.all([
            fetch(wurl, { cache: 'no-store' }).catch(() => null),
            fetch(twurl, { cache: 'no-store' }).catch(() => null),
          ]);

          if (wr && wr.ok) {
            try {
              const jw = await wr.json();
              publicWatchlist = jw.items || [];
            } catch (_) {}
          }

          if (tr && tr.ok) {
            try {
              const jt = await tr.json();
              publicTop10 = jt.items || [];
            } catch (_) {}
          }

          // If we obtained results for either, stop trying other bases
          if (publicWatchlist.length || publicTop10.length) break;
        } catch (e) {
          // ignore and try next candidate
        }
      }
      return (
        <div className="max-w-4xl mx-auto p-6">
          <div className="flex items-center gap-6 bg-white p-6 rounded-lg shadow">
            <img
              src={user.profile?.avatar_url || '/img/default-avatar.jpg'}
              alt={user.profile?.display_name || '使用者'}
              className="w-24 h-24 rounded-full object-cover"
            />
            <div>
              <h1 className="text-2xl font-bold">{user.profile?.display_name || user.email}</h1>
              <p className="text-sm text-gray-500">{user.email}</p>
              <div className="mt-3 flex gap-2 items-center">
                <Link
                  href={`/social/friends`}
                  className="inline-flex items-center px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  查看好友 / 交互
                </Link>
                <ProfileEditorClient userId={user.user_id as unknown as string} />
              </div>
            </div>
          </div>
          {/* Profile sections: About, Watched, To-Watch */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
            <section className="md:col-span-1 bg-white p-4 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-2">自我介紹</h3>
              <p className="text-sm text-gray-700">
                {user.profile && (user.profile as any).bio ? (
                  (user.profile as any).bio
                ) : (
                  <span className="text-gray-500">此使用者尚未提供自我介紹。</span>
                )}
              </p>
            </section>

            <section className="md:col-span-2 bg-white p-4 rounded-lg shadow">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">想看的電影</h3>
                <div className="text-sm text-gray-500">公開可見度：公開</div>
              </div>
              {publicWatchlist.length === 0 ? (
                <div className="text-sm text-gray-600">此使用者尚未加入任何想看的電影。</div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-3 gap-4">
                  {publicWatchlist.map((it: any) => (
                    <Link
                      key={it.id}
                      href={`/movie/${it.movie?.id || it.tmdb_id}`}
                      className="block bg-white p-2 rounded-lg hover:shadow-md transition-all duration-150"
                    >
                      <div className="flex gap-3 items-start">
                        <img
                          src={it.movie?.poster_url || '/img/default-poster.jpg'}
                          alt={it.movie?.title}
                          className="w-18 h-24 object-cover rounded flex-shrink-0"
                          style={{ width: 72, height: 100 }}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold text-sm" style={{ overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2 as any, WebkitBoxOrient: 'vertical' }}>
                            {typeof it.movie?.title === 'string' && it.movie.title.length > 48 ? it.movie.title.slice(0, 45) + '…' : it.movie?.title}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">{it.movie?.release_year || ''}</div>
                          {/* 想看清單不顯示完整簡介以保持卡片高度 */}
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </section>
          </div>

          <div className="mt-6 max-w-4xl mx-auto">
            <section className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">看過的電影 / 十大最愛</h3>
              </div>
              {publicTop10.length === 0 ? (
                <div className="text-sm text-gray-600">此使用者尚未分享任何看過或最愛的電影。</div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
                  {publicTop10.map((it: any) => (
                    <Link
                      key={it.id}
                      href={`/movie/${it.movie?.id || it.tmdb_id}`}
                      className="block bg-white p-3 rounded-lg shadow-sm hover:shadow-lg transform hover:-translate-y-1 transition-all duration-150 text-center"
                    >
                      <img
                        src={it.movie?.poster_url || '/img/default-poster.jpg'}
                        alt={it.movie?.title}
                        className="w-28 h-36 object-cover rounded mx-auto mb-2"
                      />
                      <div className="text-sm font-medium mb-1" style={{ overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2 as any, WebkitBoxOrient: 'vertical' }}>
                        {typeof it.movie?.title === 'string' && it.movie.title.length > 40 ? it.movie.title.slice(0, 37) + '…' : it.movie?.title}
                      </div>
                      <div className="text-xs text-gray-500 mb-1">Rank {it.rank}</div>
                      {it.movie?.overview ? (
                        <p className="text-xs text-gray-600 mt-1" style={{ overflow: 'hidden' }}>
                          {typeof it.movie.overview === 'string' && it.movie.overview.length > 100 ? it.movie.overview.slice(0, 97) + '…' : it.movie.overview}
                        </p>
                      ) : null}
                    </Link>
                  ))}
                </div>
              )}
            </section>
          </div>
        </div>
      );
    }

    // No successful response — render debug info for each attempt
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold mb-2">找不到該使用者（Debug）</h2>
        <p className="text-sm text-gray-600 mb-4">我向以下 URL 嘗試存取用戶資料，但都未成功：</p>
        <ul className="list-disc pl-5">
          {details.map((d, i) => (
            <li key={i} className="text-sm">
              <strong>{d.url}</strong> — status: {d.status}
              {d.text ? <div className="text-xs text-gray-500">{d.text}</div> : null}
            </li>
          ))}
        </ul>
        <div className="mt-4 text-sm text-gray-700">建議：確認後端服務是否在上述主機/埠運行，或檢查 `NEXT_PUBLIC_API_BASE` 環境變數設定。</div>
      </div>
    );
  } catch (e) {
    console.error('Error fetching profile on server:', e);
    return <div className="p-6 text-red-600">載入使用者資料時發生錯誤。</div>;
  }
}
