import { API_BASE } from "../../../lib/config";
import type { UserPublic } from "../../../lib/types/user";
import Link from 'next/link';
import ProfileEditorClient from '../../../components/ProfileEditorClient';
import { 
  EnvelopeIcon, 
  UserIcon, 
  FilmIcon, 
  TrophyIcon, 
  StarIcon,
  HeartIcon,
  SparklesIcon,
  FireIcon,
  BoltIcon,
  MoonIcon,
  SunIcon,
  BeakerIcon,
  FaceSmileIcon
} from '@heroicons/react/24/solid';
import { MovieCard } from '../../../components/MovieCard';
import { toMovieCardFormat } from '../../../lib/movieAdapter';

// 電影類型對應的圖標和顏色配置
const genreIconMap: Record<string, { icon: any; gradient: string; shadow: string }> = {
  'Action': { icon: BoltIcon, gradient: 'from-orange-500 to-red-500', shadow: 'shadow-orange-500/50' },
  'Adventure': { icon: SparklesIcon, gradient: 'from-yellow-500 to-amber-500', shadow: 'shadow-yellow-500/50' },
  'Comedy': { icon: FaceSmileIcon, gradient: 'from-pink-500 to-rose-500', shadow: 'shadow-pink-500/50' },
  'Drama': { icon: HeartIcon, gradient: 'from-red-500 to-pink-500', shadow: 'shadow-red-500/50' },
  'Horror': { icon: MoonIcon, gradient: 'from-purple-500 to-indigo-500', shadow: 'shadow-purple-500/50' },
  'Thriller': { icon: FireIcon, gradient: 'from-blue-500 to-cyan-500', shadow: 'shadow-blue-500/50' },
  'Romance': { icon: HeartIcon, gradient: 'from-rose-500 to-pink-500', shadow: 'shadow-rose-500/50' },
  'Sci-Fi': { icon: BeakerIcon, gradient: 'from-cyan-500 to-blue-500', shadow: 'shadow-cyan-500/50' },
  'Science Fiction': { icon: BeakerIcon, gradient: 'from-cyan-500 to-blue-500', shadow: 'shadow-cyan-500/50' },
  'Fantasy': { icon: SparklesIcon, gradient: 'from-purple-500 to-violet-500', shadow: 'shadow-purple-500/50' },
  'Animation': { icon: StarIcon, gradient: 'from-yellow-500 to-orange-500', shadow: 'shadow-yellow-500/50' },
  'Mystery': { icon: MoonIcon, gradient: 'from-indigo-500 to-purple-500', shadow: 'shadow-indigo-500/50' },
  'Crime': { icon: FireIcon, gradient: 'from-gray-500 to-slate-500', shadow: 'shadow-gray-500/50' },
  'Family': { icon: HeartIcon, gradient: 'from-green-500 to-emerald-500', shadow: 'shadow-green-500/50' },
  'War': { icon: BoltIcon, gradient: 'from-red-600 to-orange-600', shadow: 'shadow-red-600/50' },
  'Western': { icon: SunIcon, gradient: 'from-amber-600 to-orange-600', shadow: 'shadow-amber-600/50' },
};

// 取得電影類型的視覺配置
function getGenreConfig(genre: string) {
  return genreIconMap[genre] || { icon: FilmIcon, gradient: 'from-gray-500 to-slate-500', shadow: 'shadow-gray-500/50' };
}

export default async function OtherProfilePage({ params }: { params: { id: string } } | any) {
  const { id: userId } = await params;
  if (!userId) {
    return <div className="p-6">找不到該使用者。</div>;
  }

  try {
    // Try several candidate bases because backend may be mounted with or without /api or /api/v1
    const candidatesRaw = [API_BASE];
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
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
          <div className="max-w-7xl mx-auto p-4 sm:p-6">
            {/* 個人資訊卡片 */}
            <div className="relative bg-gradient-to-br from-gray-800/60 to-gray-700/60 backdrop-blur-md border border-gray-600/30 rounded-3xl overflow-hidden shadow-2xl mb-8">
              {/* 裝飾性背景 */}
              <div className="absolute inset-0 bg-gradient-to-r from-purple-600/10 to-pink-600/10"></div>
              
              <div className="relative p-6 sm:p-8">
                <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
                  {/* 頭像與私訊按鈕 */}
                  <div className="flex flex-col items-center gap-3 flex-shrink-0">
                    <div className="relative group">
                      <div className="w-28 h-28 sm:w-32 sm:h-32 rounded-2xl overflow-hidden ring-4 ring-gray-600/50 group-hover:ring-purple-500/50 transition-all duration-300 shadow-xl">
                        <img
                          src={user.profile?.avatar_url || '/img/default-avatar.jpg'}
                          alt={user.profile?.display_name || '使用者'}
                          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                        />
                      </div>
                      {/* 縮小的圖標 */}
                      <div className="absolute -bottom-1 -right-1 w-8 h-8 bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg flex items-center justify-center shadow-lg shadow-purple-500/30">
                        <UserIcon className="w-4 h-4 text-white" />
                      </div>
                    </div>
                    
                    {/* 私訊按鈕（頭像下方） */}
                    <Link 
                      href={`/messages?user=${user.user_id}`} 
                      className="group flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-lg transition-all duration-300 shadow-lg shadow-purple-500/30 hover:shadow-purple-500/50 hover:scale-105 text-sm"
                    >
                      <EnvelopeIcon className="w-4 h-4" />
                      <span className="font-medium">私訊</span>
                    </Link>
                  </div>
                  
                  {/* 資訊區 */}
                  <div className="flex-1 text-center sm:text-left space-y-4">
                    {/* 名字與等級積分 */}
                    <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                      <h1 className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-white via-purple-200 to-pink-200 bg-clip-text text-transparent">
                        {user.profile?.display_name || user.email}
                      </h1>
                      
                      {/* 等級與積分（優化版） */}
                      <div className="flex items-center gap-2 justify-center sm:justify-start">
                        <div className="group flex items-center gap-1.5 bg-gradient-to-br from-yellow-600/30 to-orange-600/30 backdrop-blur-sm border border-yellow-500/40 hover:border-yellow-400/60 rounded-lg px-3 py-1.5 transition-all duration-300 hover:scale-105">
                          <TrophyIcon className="w-3.5 h-3.5 text-yellow-400 group-hover:rotate-12 transition-transform" />
                          <span className="text-sm font-bold text-yellow-400">LV.{user.level || 1}</span>
                        </div>
                        <div className="group flex items-center gap-1.5 bg-gradient-to-br from-purple-600/30 to-pink-600/30 backdrop-blur-sm border border-purple-500/40 hover:border-purple-400/60 rounded-lg px-3 py-1.5 transition-all duration-300 hover:scale-105">
                          <StarIcon className="w-3.5 h-3.5 text-purple-400 group-hover:rotate-12 transition-transform" />
                          <span className="text-sm font-bold text-purple-400">{user.total_points || 0}</span>
                        </div>
                      </div>
                    </div>
          
                    
                    {/* 喜愛的電影類型 - Icon 版本 */}
                    {user.profile?.favorite_genres && user.profile.favorite_genres.length > 0 && (
                      <div className="space-y-2">
                        <div className="flex flex-wrap gap-2 justify-center sm:justify-start">
                          {user.profile.favorite_genres.map((genre: string) => {
                            const config = getGenreConfig(genre);
                            const IconComponent = config.icon;
                            return (
                              <div
                                key={genre}
                                className={`group relative flex items-center gap-2 px-3 py-2 bg-gradient-to-br ${config.gradient} bg-opacity-20 backdrop-blur-sm border border-white/20 rounded-xl transition-all duration-300 hover:scale-110 hover:shadow-lg ${config.shadow}`}
                                title={genre}
                              >
                                <IconComponent className="w-4 h-4 text-white drop-shadow-lg" />
                                <span className="text-xs font-medium text-white drop-shadow">{genre}</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                    
                    {/* 自我介紹（整合到這裡） */}
                    {user.profile && (user.profile as any).bio && (
                      <div className="space-y-2 pt-2">
                        <div className="flex items-center justify-center sm:justify-start gap-2">
                          <UserIcon className="w-4 h-4 text-blue-400" />
                          <span className="text-sm text-gray-400">自我介紹</span>
                        </div>
                        <p className="text-sm text-gray-300 leading-relaxed bg-gray-900/30 rounded-lg p-3 border border-gray-700/30">
                          {(user.profile as any).bio}
                        </p>
                      </div>
                    )}
                    
                    {/* 編輯按鈕 */}
                    <div className="pt-2">
                      <ProfileEditorClient userId={user.user_id as unknown as string} />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 十大最愛（優先顯示，使用完整 MovieCard）*/}
            <div className="mb-8">
              <div className="bg-gradient-to-br from-gray-800/60 to-gray-700/60 backdrop-blur-md border border-gray-600/30 rounded-2xl p-6 shadow-lg">
                <div className="flex items-center gap-2 mb-6">
                  <div className="w-8 h-8 bg-gradient-to-br from-pink-600 to-rose-600 rounded-lg flex items-center justify-center">
                    <TrophyIcon className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">十大最愛電影</h3>
                  {publicTop10.length > 0 && (
                    <span className="ml-auto text-sm text-gray-400">共 {publicTop10.length} 部</span>
                  )}
                </div>
                
                {publicTop10.length === 0 ? (
                  <div className="text-center py-16">
                    <TrophyIcon className="w-20 h-20 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400 text-lg">此使用者尚未設定十大最愛電影</p>
                    <p className="text-gray-500 text-sm mt-2">最愛的電影會在這裡展示</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                    {publicTop10.map((it: any) => {
                      const movieData = toMovieCardFormat({
                        ...it.movie,
                        id: it.movie?.id || it.tmdb_id,
                      });
                      
                      return (
                        <div key={it.id} className="relative">
                          {/* Rank 徽章（懸浮在 MovieCard 上方）*/}
                          <div className="absolute -top-2 -left-2 z-10 w-10 h-10 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-full flex items-center justify-center shadow-lg shadow-yellow-500/50 font-bold text-white border-2 border-white/20">
                            {it.rank}
                          </div>
                          <MovieCard movie={movieData} />
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* 想看的電影 */}
            <div>
              <div className="bg-gradient-to-br from-gray-800/60 to-gray-700/60 backdrop-blur-md border border-gray-600/30 rounded-2xl p-6 shadow-lg">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-gradient-to-br from-yellow-600 to-orange-600 rounded-lg flex items-center justify-center">
                      <FilmIcon className="w-5 h-5 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold text-white">想看的電影</h3>
                  </div>
                  <div className="flex items-center gap-3">
                    {publicWatchlist.length > 0 && (
                      <span className="text-sm text-gray-400">共 {publicWatchlist.length} 部</span>
                    )}
                    <div className="px-3 py-1 bg-green-600/20 border border-green-500/30 rounded-full">
                      <span className="text-xs text-green-400 font-medium">公開</span>
                    </div>
                  </div>
                </div>
                
                {publicWatchlist.length === 0 ? (
                  <div className="text-center py-16">
                    <FilmIcon className="w-20 h-20 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400 text-lg">此使用者尚未加入任何想看的電影</p>
                    <p className="text-gray-500 text-sm mt-2">待看清單會在這裡展示</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                    {publicWatchlist.map((it: any) => {
                      const movieData = toMovieCardFormat({
                        ...it.movie,
                        id: it.movie?.id || it.tmdb_id,
                      });
                      
                      return <MovieCard key={it.id} movie={movieData} />;
                    })}
                  </div>
                )}
              </div>
            </div>
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
