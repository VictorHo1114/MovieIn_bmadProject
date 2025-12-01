"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { getJSON, postJSON, deleteJSON } from "@/lib/http";
import { API_BASE } from "@/lib/config";
import { 
  HeartIcon, 
  StarIcon, 
  UserPlusIcon, 
  ChatBubbleLeftIcon,
  XMarkIcon,
  CheckIcon,
  EyeIcon,
  ClockIcon,
  UsersIcon
} from "@heroicons/react/24/solid";
import { cn } from "@/lib/utils/cn";

interface FriendUser {
  user_id: string;
  display_name?: string | null;
  avatar_url?: string | null;
  level?: number;
  similarity_score?: number;
}

export default function SocialPage() {
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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 px-4 py-8">
      <div className="max-w-7xl mx-auto">
        {/* 標題區 */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-white mb-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            交友中心
          </h1>
          <p className="text-gray-400">探索品味相似的影迷，建立你的電影社交圈</p>
        </motion.div>

        {error && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-4 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-yellow-300"
          >
            {error}
          </motion.div>
        )}

        {/* 現代化 Tabs */}
        <div className="mb-8 relative">
          <div className="flex items-center gap-2 flex-wrap bg-gray-800/50 backdrop-blur-sm p-2 rounded-xl border border-gray-700/50">
            {[
              { id: 'requests', label: '好友邀請', count: requests.length, icon: UserPlusIcon, color: 'red' },
              { id: 'suggested', label: '推薦好友', count: suggested.length, icon: UsersIcon, color: 'purple' },
              { id: 'friends', label: '我的好友', count: friends.length, icon: HeartIcon, color: 'pink' },
              { id: 'sent', label: '已發出', count: sentRequests.length, icon: ClockIcon, color: 'blue' },
            ].map((tabItem) => (
              <motion.button
                key={tabItem.id}
                onClick={() => setTab(tabItem.id as any)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={cn(
                  "relative px-4 py-2.5 rounded-lg font-medium transition-all duration-200 flex items-center gap-2",
                  tab === tabItem.id
                    ? "bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/30"
                    : "text-gray-300 hover:bg-gray-700/50"
                )}
              >
                <tabItem.icon className="w-5 h-5" />
                <span>{tabItem.label}</span>
                {tabItem.count > 0 && (
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className={cn(
                      "ml-1 px-2 py-0.5 text-xs font-bold rounded-full",
                      tabItem.id === 'requests' && tabItem.count > 0
                        ? "bg-red-500 text-white"
                        : "bg-gray-700 text-gray-200"
                    )}
                  >
                    {tabItem.count}
                  </motion.span>
                )}
              </motion.button>
            ))}
          </div>
        </div>

        {tab === 'requests' && (
          <motion.section 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-8"
          >
            <h2 className="text-2xl text-white font-semibold mb-6 flex items-center gap-2">
              <UserPlusIcon className="w-6 h-6 text-purple-400" />
              好友邀請
            </h2>

            {requests.length === 0 ? (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-16 bg-gray-800/30 rounded-2xl border border-gray-700/50 backdrop-blur-sm"
              >
                <UserPlusIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 text-lg mb-2">目前沒有好友邀請</p>
                <p className="text-gray-500 text-sm">去推薦好友找找志同道合的影迷吧！</p>
              </motion.div>
            ) : (
              <motion.div 
                className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                initial="hidden"
                animate="visible"
                variants={{
                  visible: {
                    transition: {
                      staggerChildren: 0.1
                    }
                  }
                }}
              >
                {requests.map((r, idx) => (
                  <motion.div
                    key={r.id}
                    variants={{
                      hidden: { opacity: 0, y: 20 },
                      visible: { opacity: 1, y: 0 }
                    }}
                    whileHover={{ y: -8, scale: 1.02 }}
                    className="group relative bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl overflow-hidden shadow-xl border border-gray-700 hover:border-purple-500 transition-all duration-300"
                  >
                    {/* 頭像區 */}
                    <div className="relative aspect-[2/3] overflow-hidden">
                      <img 
                        src={r.avatar_url ?? '/img/default-avatar.jpg'} 
                        alt={r.display_name ?? '邀請者'} 
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" 
                      />
                      {/* 漸層遮罩 */}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                      
                      {/* 新邀請標記 */}
                      <div className="absolute top-3 right-3">
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="px-3 py-1 bg-red-500 rounded-full text-white text-xs font-bold shadow-lg"
                        >
                          NEW
                        </motion.div>
                      </div>
                    </div>
                    
                    {/* 資訊區 */}
                    <div className="p-4">
                      <h3 className="text-white font-bold text-lg mb-2 line-clamp-1">
                        {r.display_name ?? '使用者'}
                      </h3>
                      {r.message && (
                        <p className="text-sm text-gray-400 mb-3 line-clamp-2">
                          "{r.message}"
                        </p>
                      )}
                      
                      {/* 按鈕組 */}
                      <div className="flex flex-col gap-2">
                        <div className="flex gap-2">
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => accept(r.id)}
                            className="flex-1 px-3 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg font-medium hover:from-green-500 hover:to-emerald-500 transition-all shadow-lg hover:shadow-green-500/50 flex items-center justify-center gap-1"
                          >
                            <CheckIcon className="w-4 h-4" />
                            接受
                          </motion.button>
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => ignore(r.id)}
                            className="flex-1 px-3 py-2 bg-gray-700 text-gray-200 rounded-lg hover:bg-gray-600 transition-all flex items-center justify-center gap-1"
                          >
                            <XMarkIcon className="w-4 h-4" />
                            忽略
                          </motion.button>
                        </div>
                        <Link 
                          href={`/profile/${r.user_id}`}
                          className="w-full px-3 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-all text-center flex items-center justify-center gap-1"
                        >
                          <EyeIcon className="w-4 h-4" />
                          查看檔案
                        </Link>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </motion.section>
        )}

        {tab === 'friends' && (
          <motion.section 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-8"
          >
            <h2 className="text-2xl text-white font-semibold mb-6 flex items-center gap-2">
              <HeartIcon className="w-6 h-6 text-pink-400" />
              我的好友
            </h2>

            {loadingFriends ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="bg-gray-800/50 rounded-2xl overflow-hidden animate-pulse">
                    <div className="aspect-[2/3] bg-gray-700" />
                    <div className="p-4 space-y-3">
                      <div className="h-4 bg-gray-700 rounded w-3/4" />
                      <div className="h-8 bg-gray-700 rounded" />
                    </div>
                  </div>
                ))}
              </div>
            ) : friends.length === 0 ? (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-16 bg-gray-800/30 rounded-2xl border border-gray-700/50 backdrop-blur-sm"
              >
                <HeartIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 text-lg mb-2">還沒有好友</p>
                <p className="text-gray-500 text-sm">試試推薦好友或搜尋使用者</p>
              </motion.div>
            ) : (
              <motion.div 
                className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                initial="hidden"
                animate="visible"
                variants={{
                  visible: {
                    transition: {
                      staggerChildren: 0.08
                    }
                  }
                }}
              >
                {friends.map((f) => (
                  <motion.div
                    key={f.user_id}
                    variants={{
                      hidden: { opacity: 0, scale: 0.9 },
                      visible: { opacity: 1, scale: 1 }
                    }}
                    whileHover={{ y: -8 }}
                    className="group"
                  >
                    <article className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl overflow-hidden shadow-xl hover:shadow-pink-500/30 transition-all duration-300 border border-gray-700 hover:border-pink-500">
                      <div className="relative aspect-[2/3] overflow-hidden">
                        <img 
                          src={f.avatar_url ?? '/img/default-avatar.jpg'} 
                          alt={f.display_name ?? '使用者'} 
                          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" 
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                        
                        {/* 等級徽章 */}
                        {f.level && (
                          <div className="absolute top-3 left-3 px-2 py-1 bg-yellow-500/90 rounded-lg flex items-center gap-1">
                            <StarIcon className="w-4 h-4 text-gray-900" />
                            <span className="text-gray-900 font-bold text-xs">LV.{f.level}</span>
                          </div>
                        )}
                      </div>
                      
                      <div className="p-4">
                        <h3 className="text-white font-bold text-lg mb-3 line-clamp-1 group-hover:text-pink-300 transition-colors">
                          {f.display_name ?? '使用者'}
                        </h3>
                        
                        {/* 圓形圖標按鈕組 */}
                        <div className="flex items-center justify-center gap-8">
                          <Link 
                            href={`/profile/${f.user_id}`}
                            title="查看檔案"
                            className="w-12 h-12 rounded-full bg-gray-700 hover:bg-gray-600 border border-gray-600 hover:border-gray-500 flex items-center justify-center transition-all shadow-lg hover:shadow-gray-500/50 group/btn"
                          >
                            <EyeIcon className="w-5 h-5 text-gray-300 group-hover/btn:text-white transition-colors" />
                          </Link>
                          <Link 
                            href={`/messages?user=${f.user_id}`}
                            title="私訊"
                            className="w-12 h-12 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 flex items-center justify-center transition-all shadow-lg hover:shadow-indigo-500/50 group/btn"
                          >
                            <ChatBubbleLeftIcon className="w-5 h-5 text-white" />
                          </Link>
                          <motion.button
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={() => unfriend(f.user_id)}
                            title="移除好友"
                            className="w-12 h-12 rounded-full bg-red-600/80 hover:bg-red-600 flex items-center justify-center transition-all shadow-lg hover:shadow-red-500/50 group/btn"
                          >
                            <XMarkIcon className="w-5 h-5 text-white" />
                          </motion.button>
                        </div>
                      </div>
                    </article>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </motion.section>
        )}

        {tab === 'suggested' && (
          <motion.section
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <h2 className="text-2xl text-white font-semibold mb-6 flex items-center gap-2">
              <UsersIcon className="w-6 h-6 text-purple-400" />
              推薦好友
            </h2>

            {loadingSuggested ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="bg-gray-800/50 rounded-2xl overflow-hidden animate-pulse">
                    <div className="aspect-[2/3] bg-gray-700" />
                    <div className="p-4 space-y-3">
                      <div className="h-4 bg-gray-700 rounded w-2/3" />
                      <div className="h-8 bg-gray-700 rounded" />
                    </div>
                  </div>
                ))}
              </div>
            ) : suggested.length === 0 ? (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-16 bg-gray-800/30 rounded-2xl border border-gray-700/50 backdrop-blur-sm"
              >
                <UsersIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 text-lg">目前沒有推薦好友</p>
              </motion.div>
            ) : (
              <motion.div 
                className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                initial="hidden"
                animate="visible"
                variants={{
                  visible: {
                    transition: {
                      staggerChildren: 0.06
                    }
                  }
                }}
              >
                {suggested.map((s) => (
                  <motion.div
                    key={s.user_id}
                    variants={{
                      hidden: { opacity: 0, y: 30 },
                      visible: { opacity: 1, y: 0 }
                    }}
                    whileHover={{ y: -8, scale: 1.02 }}
                    className="group relative bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl overflow-hidden shadow-xl border border-gray-700 hover:border-purple-500 transition-all duration-300"
                  >
                    <div className="relative aspect-[2/3] overflow-hidden">
                      <img 
                        src={s.avatar_url ?? '/img/default-avatar.jpg'} 
                        alt={s.display_name ?? '建議使用者'} 
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" 
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                      
                      {/* 品味相似度徽章 */}
                      {s.similarity_score && (
                        <div className="absolute top-3 right-3 px-3 py-1.5 bg-gradient-to-r from-pink-500 to-purple-600 rounded-full flex items-center gap-1 shadow-lg">
                          <HeartIcon className="w-4 h-4 text-white" />
                          <span className="text-white font-bold text-sm">{s.similarity_score}%</span>
                        </div>
                      )}
                      
                      {/* 等級徽章 */}
                      {s.level && (
                        <div className="absolute top-3 left-3 px-2 py-1 bg-yellow-500/90 rounded-lg flex items-center gap-1">
                          <StarIcon className="w-4 h-4 text-gray-900" />
                          <span className="text-gray-900 font-bold text-xs">LV.{s.level}</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="p-4">
                      <h3 className="text-white font-bold text-lg mb-3 line-clamp-1 group-hover:text-purple-300 transition-colors">
                        {s.display_name ?? '使用者'}
                      </h3>
                      
                      {/* 圓形圖標按鈕組 */}
                      <div className="flex items-center justify-center gap-5">
                        <Link 
                          href={`/profile/${s.user_id}`}
                          title="查看檔案"
                          className="w-12 h-12 rounded-full bg-gray-700 hover:bg-gray-600 border border-gray-600 hover:border-gray-500 flex items-center justify-center transition-all shadow-lg hover:shadow-gray-500/50 group/btn"
                        >
                          <EyeIcon className="w-5 h-5 text-gray-300 group-hover/btn:text-white transition-colors" />
                        </Link>
                        <motion.button
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => sendInvite(s.user_id)}
                          title="加為好友"
                          className="w-12 h-12 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 flex items-center justify-center transition-all shadow-lg hover:shadow-purple-500/50 group/btn"
                        >
                          <UserPlusIcon className="w-5 h-5 text-white" />
                        </motion.button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </motion.section>
        )}

        {tab === 'sent' && (
          <motion.section 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-8"
          >
            <h2 className="text-2xl text-white font-semibold mb-6 flex items-center gap-2">
              <ClockIcon className="w-6 h-6 text-blue-400" />
              已發出邀請
            </h2>
            {loadingSent ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="bg-gray-800/50 rounded-2xl overflow-hidden animate-pulse">
                    <div className="aspect-[2/3] bg-gray-700" />
                    <div className="p-4 space-y-3">
                      <div className="h-4 bg-gray-700 rounded w-1/2" />
                      <div className="h-8 bg-gray-700 rounded" />
                    </div>
                  </div>
                ))}
              </div>
            ) : sentRequests.length === 0 ? (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-16 bg-gray-800/30 rounded-2xl border border-gray-700/50 backdrop-blur-sm"
              >
                <ClockIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 text-lg">尚未發出邀請</p>
              </motion.div>
            ) : (
              <motion.div 
                className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                initial="hidden"
                animate="visible"
                variants={{
                  visible: {
                    transition: {
                      staggerChildren: 0.08
                    }
                  }
                }}
              >
                {sentRequests.map((s) => (
                  <motion.div
                    key={s.id}
                    variants={{
                      hidden: { opacity: 0, scale: 0.9 },
                      visible: { opacity: 1, scale: 1 }
                    }}
                    whileHover={{ y: -6 }}
                    className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl overflow-hidden shadow-xl border border-gray-700 hover:border-blue-500 transition-all duration-300"
                  >
                    <div className="relative aspect-[2/3] overflow-hidden">
                      <img 
                        src={s.avatar_url ?? '/img/default-avatar.jpg'} 
                        alt={s.display_name ?? '使用者'} 
                        className="w-full h-full object-cover opacity-80" 
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent" />
                      <div className="absolute top-3 right-3 px-3 py-1 bg-blue-500/90 rounded-full text-white text-xs font-bold">
                        待回應
                      </div>
                    </div>
                    <div className="p-4">
                      <h3 className="text-white font-bold text-lg mb-2 line-clamp-1">{s.display_name ?? '使用者'}</h3>
                      {s.message && (
                        <p className="text-sm text-gray-400 mb-3 line-clamp-2">"{s.message}"</p>
                      )}
                      <div className="flex gap-2">
                        <Link 
                          href={`/profile/${s.friend_id}`}
                          className="flex-1 px-3 py-2 border border-gray-600 text-gray-200 rounded-lg hover:bg-gray-700 transition-all text-center"
                        >
                          查看
                        </Link>
                        <motion.button 
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => cancelSent(s.id)}
                          className="flex-1 px-3 py-2 bg-gray-700 text-gray-200 rounded-lg hover:bg-gray-600 transition-all"
                        >
                          取消
                        </motion.button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </motion.section>
        )}
      </div>
      
      {/* 升級版 Undo Toast */}
      <AnimatePresence>
        {undoData && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.9 }}
            className="fixed bottom-6 right-6 z-50 w-96"
          >
            <div className="bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 text-white p-4 rounded-xl shadow-2xl backdrop-blur-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <CheckIcon className="w-5 h-5 text-green-400" />
                  <div className="text-sm font-medium">好友已移除</div>
                </div>
                <div className="text-xs text-gray-400">
                  剩餘 {Math.floor(remainingSeconds / 60)}:{String(remainingSeconds % 60).padStart(2, '0')}
                </div>
              </div>
              
              {/* 進度條 */}
              <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden mb-3">
                <motion.div
                  initial={{ width: '100%' }}
                  animate={{ width: `${Math.max(0, (remainingSeconds / (5 * 60)) * 100)}%` }}
                  className="h-2 bg-gradient-to-r from-green-500 to-emerald-500"
                  transition={{ duration: 1, ease: 'linear' }}
                />
              </div>
              
              <div className="flex items-center justify-end gap-2">
                <motion.button 
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={undoRemove}
                  className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-medium shadow-lg hover:from-blue-500 hover:to-indigo-500 transition-all"
                >
                  復原
                </motion.button>
                <button 
                  onClick={() => { 
                    if (undoData?.timerId) window.clearTimeout(undoData.timerId); 
                    setUndoData(null); 
                  }}
                  className="px-3 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                >
                  關閉
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
