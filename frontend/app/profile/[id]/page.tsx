import { API_BASE } from "../../../lib/config";
import type { UserPublic } from "../../../lib/types/user";
import Link from 'next/link';

export default async function OtherProfilePage({ params }: { params: { id: string } } | any) {
  const { id: userId } = await params;
  if (!userId) {
    return <div className="p-6">找不到該使用者。</div>;
  }

  try {
    const candidates = [API_BASE, 'http://127.0.0.1:8000/api/v1', 'http://localhost:8000/api/v1'];
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
              <div className="mt-3 flex gap-2">
                <Link
                  href={`/social/friends`}
                  className="inline-flex items-center px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  查看好友 / 交互
                </Link>
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
                <h3 className="text-lg font-semibold">看過的電影</h3>
                <div className="text-sm text-gray-500">公開可見度：私人</div>
              </div>
              <div className="text-sm text-gray-600">此內容僅供該使用者檢視；若想要看到朋友的看過/想看清單，請請對方開放分享或導入社交功能。</div>
            </section>
          </div>

          <div className="mt-6 max-w-4xl mx-auto">
            <section className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">想看的電影</h3>
              </div>
              <div className="text-sm text-gray-600">尚未公開任何想看的電影。</div>
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
