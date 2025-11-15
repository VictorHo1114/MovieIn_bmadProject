"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getJSON, postJSON } from "@/lib/http";
import { API_BASE } from "@/lib/config";

interface FriendUser {
  user_id: string;
  display_name?: string | null;
  avatar_url?: string | null;
}

export default function FriendsPage() {
  const [friends, setFriends] = useState<FriendUser[]>([]);
  const [suggested, setSuggested] = useState<FriendUser[]>([]);
  const [requests, setRequests] = useState<any[]>([]);
  const [loadingFriends, setLoadingFriends] = useState(true);
  const [loadingSuggested, setLoadingSuggested] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadFriends() {
      try {
        const res = await getJSON<{ items: FriendUser[]; total: number }>("/friends");
        if (!mounted) return;
        setFriends(res.items ?? []);
      } catch (e) {
        console.warn("Failed to load friends", e);
        if (!mounted) return;
        setError("無法載入好友清單（請先登入）");
      } finally {
        if (!mounted) return;
        setLoadingFriends(false);
      }
    }

    async function loadSuggested() {
      try {
        const res = await getJSON<{ items: FriendUser[]; total: number }>("/friends/suggested?limit=12");
        if (!mounted) return;
        setSuggested(res.items ?? []);
      } catch (e) {
        console.warn("Failed to load suggested friends", e);
        if (!mounted) return;
        setSuggested([]);
      } finally {
        if (!mounted) return;
        setLoadingSuggested(false);
      }
    }

    loadFriends();
    loadSuggested();
    // load incoming friend requests
    async function loadRequests() {
      try {
        const res = await getJSON<any[]>("/friends/requests");
        if (!mounted) return;
        setRequests(res ?? []);
      } catch (e) {
        console.warn("Failed to load friend requests", e);
        if (!mounted) return;
        setRequests([]);
      }
    }
    loadRequests();

    return () => { mounted = false; };
  }, []);

  const sendInvite = async (friendId: string) => {
    try {
      await postJSON("/friends/request", { friend_id: friendId, message: "嗨，我想加你為好友" });
      // 移除已邀請的建議
      setSuggested((prev) => prev.filter((p) => p.user_id !== friendId));
      alert("好友邀請已送出");
    } catch (e: any) {
      console.error(e);
      alert(`送出邀請失敗：${e.message ?? e}`);
    }
  };

  const accept = async (id: string) => {
    try {
      await postJSON(`/friends/requests/${id}/accept`, {});
      setRequests((prev) => prev.filter((r) => r.id !== id));
      // reload friends list
      const res = await getJSON<{ items: FriendUser[]; total: number }>("/friends");
      setFriends(res.items ?? []);
    } catch (e: any) {
      console.error(e);
      alert(`接受邀請失敗：${e.message ?? e}`);
    }
  };

  const ignore = async (id: string) => {
    try {
      await postJSON(`/friends/requests/${id}/ignore`, {});
      setRequests((prev) => prev.filter((r) => r.id !== id));
    } catch (e: any) {
      console.error(e);
      alert(`忽略邀請失敗：${e.message ?? e}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-6">好友</h1>

        {error && <div className="text-sm text-yellow-300 mb-4">{error}</div>}
        <section className="mb-8">
          <h2 className="text-xl text-white font-semibold mb-4">好友邀請</h2>

          {requests.length === 0 ? (
            <div className="text-gray-300 mb-4">目前沒有好友邀請。</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 mb-6">
              {requests.map((r) => (
                <div key={r.id} className="bg-gray-800 rounded-2xl overflow-hidden shadow-md border border-gray-700">
                  <div className="relative aspect-[2/3]">
                    <img src={r.avatar_url ?? '/img/default-avatar.jpg'} alt={r.display_name ?? '邀請者'} className="w-full h-full object-cover" />
                  </div>
                  <div className="p-3">
                    <h3 className="text-white font-bold text-lg line-clamp-1">{r.display_name ?? '使用者'}</h3>
                    <p className="text-sm text-gray-300 mt-2 line-clamp-2">{r.message ?? ''}</p>
                    <div className="mt-3 flex items-center space-x-2">
                      <button onClick={() => accept(r.id)} className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-500">接受</button>
                      <button onClick={() => ignore(r.id)} className="px-3 py-2 bg-gray-700 text-gray-200 rounded hover:bg-gray-600">忽略</button>
                      <Link href={`/profile/${r.user_id}`} className="px-3 py-2 border border-gray-600 text-gray-200 rounded hover:bg-gray-700">檢視</Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

        </section>

        <section className="mb-8">
          <h2 className="text-xl text-white font-semibold mb-4">我的好友</h2>

          {loadingFriends ? (
            <div className="text-white">載入中…</div>
          ) : friends.length === 0 ? (
            <div className="text-gray-300">尚未有好友，試試建議好友或搜尋使用者。</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {friends.map((f) => (
                <Link key={f.user_id} href={`/profile/${f.user_id}`} className="group">
                  <article className="bg-gray-800 rounded-2xl overflow-hidden shadow-md hover:shadow-yellow-300/30 transition-all duration-200 border border-gray-700">
                    <div className="relative aspect-[2/3]">
                      <img src={f.avatar_url ?? '/img/default-avatar.jpg'} alt={f.display_name ?? '使用者'} className="w-full h-full object-cover" />
                    </div>
                    <div className="p-3">
                      <h3 className="text-white font-bold text-lg line-clamp-1">{f.display_name ?? '使用者'}</h3>
                    </div>
                  </article>
                </Link>
              ))}
            </div>
          )}
        </section>

        <section>
          <h2 className="text-xl text-white font-semibold mb-4">建議好友</h2>

          {loadingSuggested ? (
            <div className="text-white">載入中…</div>
          ) : suggested.length === 0 ? (
            <div className="text-gray-300">目前沒有建議好友。</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {suggested.map((s) => (
                <div key={s.user_id} className="bg-gray-800 rounded-2xl overflow-hidden shadow-md border border-gray-700">
                  <div className="relative aspect-[2/3]">
                    <img src={s.avatar_url ?? '/img/default-avatar.jpg'} alt={s.display_name ?? '建議使用者'} className="w-full h-full object-cover" />
                  </div>
                  <div className="p-3">
                    <h3 className="text-white font-bold text-lg line-clamp-1">{s.display_name ?? '使用者'}</h3>
                    <div className="mt-3 flex items-center space-x-2">
                      <button
                        onClick={() => sendInvite(s.user_id)}
                        className="px-3 py-2 bg-purple-600 text-white rounded hover:bg-purple-500"
                      >
                        邀請
                      </button>
                      <Link href={`/profile/${s.user_id}`} className="px-3 py-2 border border-gray-600 text-gray-200 rounded hover:bg-gray-700">
                        檢視
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
