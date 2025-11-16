"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getJSON, postJSON, deleteJSON } from "@/lib/http";
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
  const [sentRequests, setSentRequests] = useState<any[]>([]);
  const [loadingFriends, setLoadingFriends] = useState(true);
  const [loadingSuggested, setLoadingSuggested] = useState(true);
  const [loadingRequests, setLoadingRequests] = useState(true);
  const [loadingSent, setLoadingSent] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<'requests' | 'suggested' | 'friends' | 'sent'>(() => 'requests');
  const [undoData, setUndoData] = useState<{
    friendId: string;
    timerId: number | null;
    expiresAt: number;
  } | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState<number>(0);

  useEffect(() => {
    let mounted = true;

    // fetch all lists concurrently
    const loadAll = async () => {
      await Promise.all([
        (async () => {
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
        })(),
        (async () => {
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
        })(),
        (async () => {
          try {
            const res = await getJSON<any[]>("/friends/requests");
            if (!mounted) return;
            setRequests(res ?? []);
          } catch (e) {
            console.warn("Failed to load friend requests", e);
            if (!mounted) return;
            setRequests([]);
          } finally {
            if (!mounted) return;
            setLoadingRequests(false);
          }
        })(),
        (async () => {
          try {
            const res = await getJSON<any[]>("/friends/requests/sent");
            if (!mounted) return;
            setSentRequests(res ?? []);
          } catch (e) {
            console.warn("Failed to load sent requests", e);
            if (!mounted) return;
            setSentRequests([]);
          } finally {
            if (!mounted) return;
            setLoadingSent(false);
          }
        })(),
      ]);
    };

    loadAll();

    // Polling: refresh incoming requests every 30s and notify NavBar
    const interval = setInterval(async () => {
      try {
        const res = await getJSON<any[]>("/friends/requests");
        if (!mounted) return;
        setRequests(res ?? []);
        window.dispatchEvent(new CustomEvent('friendRequestsUpdated'));
      } catch (e) {
        // ignore
      }
    }, 30000);

    return () => { mounted = false; clearInterval(interval); };
  }, []);

  const sendInvite = async (friendId: string) => {
    try {
      await postJSON("/friends/request", { friend_id: friendId, message: "嗨，我想加你為好友" });
      // 移除已邀請的建議
      setSuggested((prev) => prev.filter((p) => p.user_id !== friendId));
      // refresh sent requests and incoming requests
      try {
        const sent = await getJSON<any[]>("/friends/requests/sent");
        setSentRequests(sent ?? []);
      } catch {}
      try {
        const incoming = await getJSON<any[]>("/friends/requests");
        setRequests(incoming ?? []);
      } catch {}
      // notify NavBar
      window.dispatchEvent(new CustomEvent('friendRequestsUpdated'));
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
      // refresh sent requests
      try {
        const sent = await getJSON<any[]>("/friends/requests/sent");
        setSentRequests(sent ?? []);
      } catch {}
      window.dispatchEvent(new CustomEvent('friendRequestsUpdated'));
    } catch (e: any) {
      console.error(e);
      alert(`接受邀請失敗：${e.message ?? e}`);
    }
  };

  const ignore = async (id: string) => {
    try {
      await postJSON(`/friends/requests/${id}/ignore`, {});
      setRequests((prev) => prev.filter((r) => r.id !== id));
      window.dispatchEvent(new CustomEvent('friendRequestsUpdated'));
    } catch (e: any) {
      console.error(e);
      alert(`忽略邀請失敗：${e.message ?? e}`);
    }
  };

  const unfriend = async (friendId: string) => {
    const ok = confirm('確定要移除此好友嗎？你可以在 5 分鐘內復原。');
    if (!ok) return;
    try {
      await deleteJSON(`/friends/${friendId}`);
      // optimistically remove locally
      setFriends((prev) => prev.filter((f) => f.user_id !== friendId));
      // notify NavBar and other listeners
      window.dispatchEvent(new CustomEvent('friendRequestsUpdated'));

      // show undo UI for 5 minutes
      const expiresAt = Date.now() + 5 * 60 * 1000;
      const timer = window.setTimeout(() => {
        setUndoData(null);
      }, 5 * 60 * 1000);
      setUndoData({ friendId, timerId: timer as unknown as number, expiresAt });
    } catch (e: any) {
      console.error('Failed to remove friend', e);
      alert(`移除好友失敗：${e.message ?? e}`);
    }
  };

  const undoRemove = async () => {
    if (!undoData) return;
    const { friendId, timerId } = undoData;
    try {
      await postJSON(`/friends/${friendId}/restore`, {});
      // refresh friends list
      try {
        const res = await getJSON<{ items: FriendUser[]; total: number }>("/friends");
        setFriends(res.items ?? []);
      } catch (e) {
        // ignore
      }
      window.dispatchEvent(new CustomEvent('friendRequestsUpdated'));
      if (timerId) window.clearTimeout(timerId);
      setUndoData(null);
      alert('已復原好友關係');
    } catch (e: any) {
      console.error('Failed to restore friend', e);
      alert(`復原失敗：${e.message ?? e}`);
    }
  };

  // countdown effect for undo snackbar
  useEffect(() => {
    if (!undoData) {
      setRemainingSeconds(0);
      return;
    }
    const tick = () => {
      const rem = Math.max(0, Math.ceil((undoData.expiresAt - Date.now()) / 1000));
      setRemainingSeconds(rem);
      if (rem <= 0) {
        setUndoData(null);
      }
    };
    tick();
    const iv = window.setInterval(tick, 1000);
    return () => window.clearInterval(iv);
  }, [undoData]);

  // Cancel a sent pending request
  const cancelSent = async (friendshipId: string) => {
    const ok = confirm('確定要取消此邀請？');
    if (!ok) return;
    try {
      await deleteJSON(`/friends/requests/${friendshipId}`);
      setSentRequests((prev) => prev.filter((s) => s.id !== friendshipId));
      window.dispatchEvent(new CustomEvent('friendRequestsUpdated'));
      alert('已取消邀請');
    } catch (e: any) {
      console.error('Failed to cancel sent request', e);
      alert(`取消邀請失敗：${e.message ?? e}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-6">好友</h1>

        {error && <div className="text-sm text-yellow-300 mb-4">{error}</div>}

        {/* Tabs */}
        <div className="mb-6 flex items-center gap-3">
          <button
            onClick={() => setTab('requests')}
            className={`px-3 py-2 rounded ${tab === 'requests' ? 'bg-purple-600 text-white' : 'text-gray-300 bg-gray-800'}`}>
            好友邀請 <span className="ml-2 bg-red-600 text-white rounded-full px-2 text-xs">{requests.length}</span>
          </button>
          <button
            onClick={() => setTab('suggested')}
            className={`px-3 py-2 rounded ${tab === 'suggested' ? 'bg-purple-600 text-white' : 'text-gray-300 bg-gray-800'}`}>
            推薦好友 <span className="ml-2 text-gray-200 rounded-full px-2 text-xs">{suggested.length}</span>
          </button>
          <button
            onClick={() => setTab('friends')}
            className={`px-3 py-2 rounded ${tab === 'friends' ? 'bg-purple-600 text-white' : 'text-gray-300 bg-gray-800'}`}>
            我的好友 <span className="ml-2 text-gray-200 rounded-full px-2 text-xs">{friends.length}</span>
          </button>
          <button
            onClick={() => setTab('sent')}
            className={`px-3 py-2 rounded ${tab === 'sent' ? 'bg-purple-600 text-white' : 'text-gray-300 bg-gray-800'}`}>
            已發出邀請 <span className="ml-2 text-gray-200 rounded-full px-2 text-xs">{sentRequests.length}</span>
          </button>
        </div>

        {tab === 'requests' && (
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
        )}

        {tab === 'friends' && (
          <section className="mb-8">
            <h2 className="text-xl text-white font-semibold mb-4">我的好友</h2>

            {loadingFriends ? (
              <div className="text-white">載入中…</div>
            ) : friends.length === 0 ? (
              <div className="text-gray-300">尚未有好友，試試建議好友或搜尋使用者。</div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {friends.map((f) => (
                  <div key={f.user_id} className="group">
                    <article className="bg-gray-800 rounded-2xl overflow-hidden shadow-md hover:shadow-yellow-300/30 transition-all duration-200 border border-gray-700">
                      <div className="relative aspect-[2/3]">
                        <img src={f.avatar_url ?? '/img/default-avatar.jpg'} alt={f.display_name ?? '使用者'} className="w-full h-full object-cover" />
                      </div>
                      <div className="p-3 flex items-center justify-between">
                        <div>
                          <h3 className="text-white font-bold text-lg line-clamp-1">{f.display_name ?? '使用者'}</h3>
                        </div>
                        <div className="flex items-center gap-2">
                          <Link href={`/profile/${f.user_id}`} className="px-3 py-1 border border-gray-600 text-gray-200 rounded hover:bg-gray-700">檢視</Link>
                          <Link href={`/messages?user=${f.user_id}`} className="px-3 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-500">私訊</Link>
                          <button
                            onClick={() => unfriend(f.user_id)}
                            className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-500"
                          >
                            移除
                          </button>
                        </div>
                      </div>
                    </article>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {tab === 'suggested' && (
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
        )}

        {tab === 'sent' && (
          <section className="mb-8">
            <h2 className="text-xl text-white font-semibold mb-4">已發出邀請</h2>
            {loadingSent ? (
              <div className="text-white">載入中…</div>
            ) : sentRequests.length === 0 ? (
              <div className="text-gray-300">尚未發出邀請。</div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {sentRequests.map((s) => (
                  <div key={s.id} className="bg-gray-800 rounded-2xl overflow-hidden shadow-md border border-gray-700">
                    <div className="relative aspect-[2/3]">
                      <img src={s.avatar_url ?? '/img/default-avatar.jpg'} alt={s.display_name ?? '使用者'} className="w-full h-full object-cover" />
                    </div>
                    <div className="p-3">
                      <h3 className="text-white font-bold text-lg line-clamp-1">{s.display_name ?? '使用者'}</h3>
                      <p className="text-sm text-gray-300 mt-2 line-clamp-2">{s.message ?? ''}</p>
                      <div className="mt-3 flex items-center space-x-2">
                        <Link href={`/profile/${s.friend_id}`} className="px-3 py-2 border border-gray-600 text-gray-200 rounded hover:bg-gray-700">檢視</Link>
                        <button onClick={() => cancelSent(s.id)} className="px-3 py-2 bg-gray-700 text-gray-200 rounded hover:bg-gray-600">取消</button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}
      </div>
        {undoData && (
          <div className="fixed bottom-6 right-6 z-50 w-80">
            <div className="bg-white/95 text-gray-900 p-3 rounded-lg shadow-lg flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">好友已移除</div>
                <div className="text-xs text-gray-500">剩餘 {Math.floor(remainingSeconds / 60)}:{String(remainingSeconds % 60).padStart(2, '0')}</div>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded overflow-hidden">
                <div
                  className="h-2 bg-green-500"
                  style={{ width: `${Math.max(0, (remainingSeconds / (5 * 60)) * 100)}%` }}
                />
              </div>
              <div className="flex items-center justify-end gap-2">
                <button onClick={undoRemove} className="px-3 py-1 bg-blue-600 text-white rounded">復原</button>
                <button onClick={() => { if (undoData?.timerId) window.clearTimeout(undoData.timerId); setUndoData(null); }} className="px-2 py-1 text-sm text-gray-600">關閉</button>
              </div>
            </div>
          </div>
        )}
    </div>
  );
}
