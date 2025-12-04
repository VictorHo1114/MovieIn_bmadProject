"use client";

import React from 'react';
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { API_BASE } from "@/lib/config";
import { postJSON } from '@/lib/http';
import { Api } from '@/lib/api';
import { useWebSocket, useUserOnlineStatus } from "@/hooks/useWebSocket";
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChatBubbleLeftRightIcon, 
  PaperAirplaneIcon, 
  UserGroupIcon,
  ArrowLeftIcon,
  EllipsisVerticalIcon,
  CheckIcon,
  CheckCircleIcon
} from '@heroicons/react/24/solid';
import { UserCircleIcon } from '@heroicons/react/24/outline';

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean; error?: Error }>{
  constructor(props: any){
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: any) {
    // Log so developer can inspect terminal / console
    console.error('ErrorBoundary caught error:', error, info);
  }

  reset = () => this.setState({ hasError: false, error: undefined });

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-900 text-white p-6">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-2xl font-bold mb-4">發生錯誤</h1>
            <div className="bg-red-700 p-4 rounded mb-4">應用的某個區域發生錯誤，已被攔截以避免開發畫面崩潰。</div>
            <div className="mb-4">
              <button
                onClick={() => { this.reset(); window.location.reload(); }}
                className="px-4 py-2 bg-indigo-600 rounded"
              >重新載入頁面</button>
            </div>
            <div className="text-sm text-gray-300">請將開發工具的錯誤訊息貼給我以便我做進一步調查。</div>
          </div>
        </div>
      );
    }
    return this.props.children as any;
  }
}

function MessagesContent() {
  const search = useSearchParams();
  const userId = search?.get("user") || null;

  const [messages, setMessages] = useState<any[]>([]);
  const RECENT_LIMIT = 100;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [otherName, setOtherName] = useState<string | null>(null);
  const [otherAvatar, setOtherAvatar] = useState<string | null>(null);
  const [conversations, setConversations] = useState<any[] | null>(null);
  const [conversationsLoading, setConversationsLoading] = useState<boolean>(false);
  const [sending, setSending] = useState(false);
  const [newMessagesCount, setNewMessagesCount] = useState(0);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const isAtBottomRef = useRef<boolean>(true);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const lastMessageRef = useRef<HTMLDivElement | null>(null);
  const knownIdsRef = useRef<Set<string>>(new Set());
  
  // ✨ WebSocket 整合：移除 pollingRef, convPollRef, pausePollRef, isLoadingRef
  const [token, setToken] = useState<string | null>(null);
  
  // WebSocket Hook
  const { isConnected, sendMessage: wsSendMessage } = useWebSocket({
    token,
    autoConnect: true,
    onMessage: (message) => {
      console.log("[Messages] 收到 WebSocket 訊息:", message);
      
      // 處理新訊息 - 放寬過濾條件，只要涉及當前對話就接收
      if (message.type === "new_message" && message.data) {
        const newMsg = message.data;
        console.log("[Messages] 新訊息詳情:", {
          newMsg,
          currentUserId,
          userId,
          shouldAccept: !userId || newMsg.sender_id === userId || newMsg.recipient_id === userId || newMsg.sender_id === currentUserId || newMsg.recipient_id === currentUserId
        });
        
        // 更寬鬆的接收條件：只要訊息涉及當前用戶或當前對話就接收
        const isRelevant = !userId || 
          newMsg.sender_id === userId || 
          newMsg.recipient_id === userId || 
          newMsg.sender_id === currentUserId || 
          newMsg.recipient_id === currentUserId;
        
        if (isRelevant) {
          setMessages((prev) => {
            // 檢查是否已存在（避免重複）
            const exists = prev.some((m) => String(m.id) === String(newMsg.id));
            if (exists) {
              console.log("[Messages] 訊息已存在，跳過");
              return prev;
            }
            
            // 替換 local- 開頭的臨時訊息
            const matchedIndex = prev.findIndex((m) => 
              String(m.id).startsWith('local-') && m.body === newMsg.body
            );
            
            if (matchedIndex !== -1) {
              console.log("[Messages] 替換臨時訊息");
              const updated = [...prev];
              updated[matchedIndex] = newMsg;
              return updated;
            }
            
            // 新增訊息
            console.log("[Messages] 新增訊息到列表");
            const merged = [...prev, newMsg];
            
            // 如果不在底部且訊息是對方發的，增加新訊息計數
            if (!isAtBottomRef.current && newMsg.sender_id !== currentUserId) {
              setNewMessagesCount((n) => n + 1);
            } else {
              // 在底部時立即滾動
              setTimeout(() => scrollToBottomNow(), 50);
            }
            
            return merged.length > RECENT_LIMIT 
              ? merged.slice(merged.length - RECENT_LIMIT) 
              : merged;
          });
          
          // 如果在底部且是收到的訊息，自動標記為已讀
          if (isAtBottomRef.current && newMsg.sender_id !== currentUserId && userId) {
            setTimeout(() => {
              Api.messages.markRead(userId as string, newMsg.id).then((res) => {
                window.dispatchEvent(new CustomEvent('conversationsUpdated', { detail: res }));
              }).catch(() => {});
            }, 300);
          }
        }
      }
      
      // 處理發送確認 - 立即更新 UI
      if (message.type === "message_sent" && message.data) {
        const sentMsg = message.data;
        console.log("[Messages] 訊息發送確認:", sentMsg);
        
        // 重要：解除發送狀態
        setSending(false);
        
        setMessages((prev) => {
          console.log("[Messages] 當前訊息列表:", prev.map(m => ({ id: m.id, body: m.body })));
          console.log("[Messages] 尋找臨時訊息 body:", sentMsg.body);
          
          // 先移除所有相同內容的臨時訊息（避免重複）
          const withoutTemp = prev.filter((m) => {
            const isTemp = String(m.id).startsWith('local-') && m.body === sentMsg.body;
            if (isTemp) {
              console.log("[Messages] ✅ 找到並移除臨時訊息:", m.id);
            }
            return !isTemp;
          });
          
          console.log("[Messages] 移除臨時訊息後:", withoutTemp.length, "則");
          
          // 檢查是否已存在正式訊息
          const exists = withoutTemp.some((m) => String(m.id) === String(sentMsg.id));
          if (exists) {
            console.log("[Messages] 正式訊息已存在，跳過新增");
            return withoutTemp;
          }
          
          // 加入正式訊息
          console.log("[Messages] ✅ 加入正式訊息:", sentMsg.id);
          const updated = [...withoutTemp, sentMsg];
          return updated.length > RECENT_LIMIT 
            ? updated.slice(updated.length - RECENT_LIMIT) 
            : updated;
        });
        
        // 立即滾動到底部
        setTimeout(() => scrollToBottomNow(), 50);
      }
    },
    onConnect: () => {
      console.log("[Messages] ✅ WebSocket 已連線");
    },
    onDisconnect: () => {
      console.log("[Messages] ⚠️ WebSocket 已斷線");
    },
  });
  
  // 在線狀態
  const { isUserOnline } = useUserOnlineStatus();

  // 取得當前用戶的 token 和 ID（只執行一次）
  useEffect(() => {
    (async () => {
      try {
        const storedToken = localStorage.getItem("authToken");
        if (storedToken) {
          setToken(storedToken);
          // 安全日誌：不顯示完整 token
          console.log("[Messages] Token 已載入 (length:", storedToken.length, ")");
        }
        
        // 取得當前用戶 ID
        const res = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${storedToken}` }
        });
        if (res.ok) {
          const data = await res.json();
          const uid = data.user_id || data.id || null;
          setCurrentUserId(uid);
          console.log("[Messages] 當前用戶 ID:", uid);
        }
      } catch (e) {
        console.error("[Messages] 無法取得用戶資訊:", e);
      }
    })();
  }, []);

  // 載入對話歷史（僅在選擇用戶時載入一次）
  useEffect(() => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    setOtherName(null);
    setNewMessagesCount(0);
    
    (async () => {
      try {
        const js = await Api.messages.getConversation(userId as string).catch((e) => { throw e; });
        const jsAny: any = js;
        const items: any[] = Array.isArray(jsAny) ? jsAny : (jsAny.items || jsAny || []);
        const recent = items.slice(-RECENT_LIMIT);
        setMessages(recent);
        
        // 記錄已知訊息 ID
        try {
          knownIdsRef.current = new Set(recent.filter((m: any) => !String(m.id).startsWith('local-')).map((m: any) => String(m.id)));
        } catch (e) {}
        
        // 標記為已讀
        (async () => {
          try {
            const lastId = items.length ? items[items.length - 1].id : undefined;
            const res = await Api.messages.markRead(userId as string, lastId);
            let uc: any = null;
            try {
              uc = await Api.messages.unreadCount();
            } catch (err) {
              uc = null;
            }
            const detail = Object.assign({}, res || {}, { unreadCount: uc?.count });
            window.dispatchEvent(new CustomEvent('conversationsUpdated', { detail }));
          } catch (e) {
            // ignore
          }
        })();
      } catch (e: any) {
        setError(String(e?.message ?? e));
        setMessages([]);
      } finally {
        setLoading(false);
      }
    })();

    // 載入對方的顯示名稱和頭像
    (async () => {
      try {
        const p = await Api.profile.getById(userId as string);
        console.log("[Messages] 載入對方 Profile:", p);
        const name = p?.profile?.display_name || p?.email?.split('@')[0] || null;
        const avatar = p?.profile?.avatar_url || null;
        console.log("[Messages] 對方資訊:", { name, avatar, fullProfile: p?.profile });
        setOtherName(name);
        setOtherAvatar(avatar);
      } catch (e) {
        console.error("[Messages] 載入對方 Profile 失敗:", e);
      }
    })();

    // ✅ WebSocket 取代了輪詢，不需要 setInterval
  }, [userId]);

  // scroll to bottom whenever messages change
  useEffect(() => {
    // if the user has manually scrolled up (isAtBottomRef === false), do not auto-scroll
    if (!isAtBottomRef.current) return;

    // if we have a direct ref to the last message, scroll it into view.
    if (lastMessageRef.current) {
      try {
        lastMessageRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
      } catch (e) {}
      return;
    }
    if (!containerRef.current) return;
    // small timeout to allow DOM update
      const t = window.setTimeout(() => {
      try {
        containerRef.current?.scrollTo({ top: containerRef.current.scrollHeight, behavior: 'smooth' });
      } catch (e) {}
    }, 80);
    return () => window.clearTimeout(t);
  }, [messages.length]);

  // helper to scroll to bottom immediately (used on initial load / when opening a conversation)
  const scrollToBottomNow = () => {
    try {
      if (lastMessageRef.current) {
        lastMessageRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
        return;
      }
      if (containerRef.current) {
        containerRef.current.scrollTo({ top: containerRef.current.scrollHeight, behavior: 'smooth' });
      }
    } catch (e) {
      // ignore
    }
  };

  // Ensure when entering a conversation we scroll to bottom once after load (even if no new messages)
  useEffect(() => {
    if (!userId) return;
    // wait until loading finishes, then scroll to bottom
    if (loading) return;
    const t = window.setTimeout(() => scrollToBottomNow(), 60);
    // mark that we are at bottom after initial scroll
    isAtBottomRef.current = true;
    return () => window.clearTimeout(t);
  }, [userId, loading]);

  // handle user manual scrolling: if user scrolls away from bottom, disable auto-scroll
  const onContainerScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget;
    const threshold = 80; // px from bottom considered "at bottom"
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight <= threshold;
    isAtBottomRef.current = atBottom;
    if (atBottom) {
      // when user scrolls back to bottom, clear any unseen counter and mark read
      setNewMessagesCount(0);
      (async () => {
        try {
          const lastId = messages.length ? messages[messages.length - 1].id : undefined;
          if (lastId && userId) {
            const res = await Api.messages.markRead(userId as string, lastId).catch(() => null);
            if (res) window.dispatchEvent(new CustomEvent('conversationsUpdated', { detail: res }));
          }
        } catch (e) {}
      })();
    }
  };

  // visibility / focus handlers: when user returns to the page, mark conversation as read up to last message
  useEffect(() => {
    if (!userId) return;
    const markCurrentAsRead = async () => {
      try {
        if (!messages || messages.length === 0) return;
        const lastId = messages[messages.length - 1].id;
        if (!lastId) return;
        // Only mark as read when the user is at (or near) the bottom of the chat.
        // If the user is scrolled up we should NOT auto-mark as read on visibility/focus.
        if (!isAtBottomRef.current) {
          // notify other parts that the conversation was seen (page visible) but not marked read
          window.dispatchEvent(new CustomEvent('conversationsUpdated', { detail: { visible: true, marked: false } }));
          return;
        }
        const res = await Api.messages.markRead(userId as string, lastId).catch(() => null);
        if (res) window.dispatchEvent(new CustomEvent('conversationsUpdated', { detail: res }));
      } catch (e) {
        // ignore
      }
    };

    const onVisibility = () => {
      if (document.visibilityState === 'visible') markCurrentAsRead();
    };
    const onFocus = () => markCurrentAsRead();

    document.addEventListener('visibilitychange', onVisibility);
    window.addEventListener('focus', onFocus);

    return () => {
      document.removeEventListener('visibilitychange', onVisibility);
      window.removeEventListener('focus', onFocus);
    };
  }, [userId, messages]);

  // load current user id (if authenticated) for message alignment and sender identity
  useEffect(() => {
    (async () => {
      try {
        const me = await Api.profile.me();
        if (me && (me as any).user_id) setCurrentUserId((me as any).user_id as string);
      } catch (e) {
        // ignore (user not authenticated)
      }
    })();
  }, []);

  // when no userId is selected, try to load recent conversations list
  useEffect(() => {
    if (userId) return;

    const loadConversations = async () => {
      setConversationsLoading(true);
      try {
        const js = await Api.messages.getConversations();
        const jsAny: any = js;
        const items: any[] = Array.isArray(jsAny) ? jsAny : (jsAny.items || jsAny || []);
        console.log("[Messages] 載入對話列表:", items);
        // 檢查每個對話是否有頭像
        items.forEach((item, idx) => {
          console.log(`[Messages] 對話 ${idx}:`, {
            user_id: item.user_id,
            display_name: item.display_name,
            avatar_url: item.avatar_url,
            hasAvatar: !!item.avatar_url
          });
        });
        setConversations(items);
      } catch (e) {
        console.error("[Messages] 載入對話列表失敗:", e);
        setConversations([]);
      } finally {
        setConversationsLoading(false);
      }
    };

    // initial load
    loadConversations();

    // refresh when other parts of app dispatch updates (but debounce to avoid excessive calls)
    let debounceTimer: number | null = null;
    const handleConvUpdated = (ev: Event) => {
      try {
        // Debounce: only reload after 500ms of no events to avoid multiple rapid reloads
        if (debounceTimer) window.clearTimeout(debounceTimer);
        debounceTimer = window.setTimeout(() => {
          loadConversations();
          debounceTimer = null;
        }, 500);
      } catch (e) {
        loadConversations();
      }
    };
    window.addEventListener('conversationsUpdated', handleConvUpdated as EventListener);

    // ✅ WebSocket 取代輪詢：新訊息會透過 WebSocket 推送，觸發 conversationsUpdated 事件
    // 不再需要 10 秒輪詢

    return () => {
      window.removeEventListener('conversationsUpdated', handleConvUpdated as EventListener);
    };
  }, [userId]);

  const send = async () => {
    if (!userId) return alert('請提供收件人 ID');
    if (!text.trim()) return;
    if (sending) return;
    setSending(true);
    
    const messageBody = text.trim();
    const tempId = `local-${Date.now()}-${Math.random()}`;
    
    // 立即清空輸入框
    setText("");
    
    // 立即顯示樂觀 UI（不等 WebSocket）
    const optimisticMsg = {
      id: tempId,
      sender_id: currentUserId ?? 'me',
      recipient_id: userId,
      body: messageBody,
      created_at: new Date().toISOString(),
      is_read: false
    };
    
    setMessages((prev) => {
      const merged = [...prev, optimisticMsg];
      return merged.length > RECENT_LIMIT 
        ? merged.slice(merged.length - RECENT_LIMIT) 
        : merged;
    });
    
    // 立即滾動到底部
    isAtBottomRef.current = true;
    setTimeout(() => scrollToBottomNow(), 10);
    
    try {
      // ✨ 優先使用 WebSocket 發送
      if (isConnected && wsSendMessage) {
        console.log("[Messages] 📤 透過 WebSocket 發送訊息");
        const success = wsSendMessage(userId, messageBody);
        
        if (success) {
          // 不在這裡 setSending(false)，等待 message_sent 確認
          // WebSocket 會處理訊息確認，替換臨時訊息
          return;
        }
      }
      
      // Fallback: WebSocket 未連線，使用傳統 HTTP POST
      console.log("[Messages] Fallback to HTTP POST");
      const js: any = await postJSON('/messages', { recipient_id: userId, body: messageBody });
      const inserted = js.item || js;
      
      if (inserted && inserted.id) {
        console.debug('[messages.send] server returned inserted id=', String(inserted.id));
        setMessages((prev) => {
          // 移除臨時訊息（避免重疊）
          const withoutTemp = prev.filter((m) => 
            !(String(m.id).startsWith('local-') && m.body === messageBody)
          );
          // 添加正式訊息
          const merged = [...withoutTemp, inserted];
          return merged.length > RECENT_LIMIT 
            ? merged.slice(merged.length - RECENT_LIMIT) 
            : merged;
        });
      } else {
        console.debug('[messages.send] server did not return inserted id, keeping local placeholder');
        // 如果沒有返回 ID，保持原有的臨時訊息
      }
      
      // 滾動到底部
      try { 
        isAtBottomRef.current = true; 
        scrollToBottomNow(); 
      } catch (e) {}
      
      // 通知其他組件更新對話列表
      try {
        window.dispatchEvent(new CustomEvent('conversationsUpdated', { detail: { sent: true } }));
      } catch (e) {}
      
    } catch (e: any) {
      const msg = String(e.message ?? e);
      if (msg.includes('[401]') || msg.toLowerCase().includes('not authenticated')) {
        alert('請先登入後再傳送私訊（未驗證）。');
        setText(messageBody);
        setSending(false);
        return;
      }
      console.error('[messages.send] error:', e);
      alert(`發送失敗: ${e.message || e}`);
      setText(messageBody);
    } finally {
      setSending(false);
      try { textareaRef.current?.focus(); } catch (e) {}
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      <div className="max-w-5xl mx-auto p-4 sm:p-6">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-6"
        >
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-pink-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30">
              <ChatBubbleLeftRightIcon className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                私訊
              </h1>
              <p className="text-sm text-gray-400">與好友即時聊天</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Link 
              href="/social" 
              className="flex items-center gap-2 px-4 py-2 bg-gray-700/50 backdrop-blur-sm hover:bg-gray-700 rounded-lg transition-all duration-300 border border-gray-600/30"
            >
              <UserGroupIcon className="w-5 h-5" />
              <span className="hidden sm:inline">好友</span>
            </Link>
          </div>
        </motion.div>

        {!userId ? (
          // ═══════════════════════════════════════════════════════════
          // 對話列表（未選擇用戶時）
          // ═══════════════════════════════════════════════════════════
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            {conversations === null && !conversationsLoading ? (
              <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 p-8 rounded-2xl text-center">
                <ChatBubbleLeftRightIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400">請從好友列表或個人頁面點選「私訊」開始聊天</p>
              </div>
            ) : conversations && conversations.length === 0 ? (
              <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 p-8 rounded-2xl text-center">
                <UserCircleIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 mb-2">目前沒有對話</p>
                <p className="text-sm text-gray-500">前往好友頁面開始聊天吧！</p>
              </div>
            ) : (
              <div className="bg-gray-800/30 backdrop-blur-sm border border-gray-700/30 p-4 rounded-2xl">
                <div className="mb-4 flex items-center justify-between">
                  <div className="text-lg font-semibold text-gray-200">最近對話</div>
                  {conversationsLoading && (
                    <div className="text-sm text-gray-400">載入中...</div>
                  )}
                </div>
                
                <motion.div 
                  className="flex flex-col gap-2"
                  initial="hidden"
                  animate="visible"
                  variants={{
                    visible: { transition: { staggerChildren: 0.05 } }
                  }}
                >
                  <AnimatePresence>
                    {(conversations || []).map((c, idx) => (
                      <motion.div
                        key={c.user_id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        transition={{ duration: 0.2, delay: idx * 0.03 }}
                        whileHover={{ scale: 1.01, x: 4 }}
                        className="group relative bg-gradient-to-r from-gray-700/40 to-gray-800/40 backdrop-blur-sm hover:from-gray-700/60 hover:to-gray-800/60 p-4 rounded-xl border border-gray-600/30 hover:border-purple-500/40 transition-all duration-300 cursor-pointer"
                      >
                        <div className="flex items-center gap-4">
                          {/* 頭像區 */}
                          <Link 
                            href={`/profile/${c.user_id}`}
                            onClick={(e) => e.stopPropagation()}
                            className="flex-shrink-0 relative"
                          >
                            <div className="relative w-14 h-14 rounded-full overflow-hidden ring-2 ring-gray-600 group-hover:ring-purple-500/50 transition-all duration-300">
                              <img 
                                src={c.avatar_url || '/img/default-avatar.jpg'} 
                                alt={c.display_name || '用戶'}
                                className="w-full h-full object-cover"
                              />
                            </div>
                            {/* 在線狀態 */}
                            {c.is_online && (
                              <span className="absolute bottom-0 right-0 w-4 h-4 bg-green-500 border-2 border-gray-800 rounded-full shadow-lg shadow-green-500/50"></span>
                            )}
                          </Link>
                          
                          {/* 訊息內容區 */}
                          <Link 
                            href={`/messages?user=${c.user_id}`}
                            className="flex-1 min-w-0"
                          >
                            <div className="flex items-center gap-2 mb-1">
                              <div className="font-semibold text-white truncate group-hover:text-purple-300 transition-colors">
                                {c.display_name || c.user_id}
                              </div>
                              {c.is_online && (
                                <span className="flex items-center gap-1 text-xs text-green-400 bg-green-500/10 px-2 py-0.5 rounded-full">
                                  <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                                  在線
                                </span>
                              )}
                            </div>
                            <div className="text-sm text-gray-400 truncate">{c.last_message || '開始對話...'}</div>
                          </Link>
                          
                          {/* 未讀標記 */}
                          {c.unread > 0 && (
                            <motion.div 
                              initial={{ scale: 0 }}
                              animate={{ scale: 1 }}
                              className="flex-shrink-0 flex items-center justify-center min-w-[24px] h-6 px-2 text-xs font-bold rounded-full bg-gradient-to-r from-red-600 to-pink-600 text-white shadow-lg shadow-red-500/30"
                            >
                              {c.unread > 99 ? '99+' : c.unread}
                            </motion.div>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </motion.div>
              </div>
            )}
          </motion.div>
        ) : (
          // ═══════════════════════════════════════════════════════════
          // 對話視窗（選擇特定用戶後）
          // ═══════════════════════════════════════════════════════════
          <>
            {/* 對話標題列 */}
            <motion.div 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 bg-gradient-to-r from-gray-800/60 to-gray-700/60 backdrop-blur-md p-4 rounded-2xl border border-gray-600/30 shadow-lg"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {/* 返回按鈕 */}
                  <Link 
                    href="/messages"
                    className="w-10 h-10 flex items-center justify-center bg-gray-700/50 hover:bg-gray-600/50 rounded-full transition-all duration-300 hover:scale-110"
                  >
                    <ArrowLeftIcon className="w-5 h-5" />
                  </Link>
                  
                  {/* 對方頭像與資訊 */}
                  <Link href={`/profile/${userId}`} className="flex-shrink-0 relative group">
                    <div className="relative w-12 h-12 rounded-full overflow-hidden ring-2 ring-gray-600 group-hover:ring-purple-500/70 transition-all duration-300">
                      <img 
                        src={otherAvatar || '/img/default-avatar.jpg'} 
                        alt={otherName || '用戶'}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    {/* 在線狀態 */}
                    {userId && isUserOnline(userId) && (
                      <span className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-green-500 border-2 border-gray-800 rounded-full shadow-lg shadow-green-500/50"></span>
                    )}
                  </Link>
                  
                  <div className="flex-1 min-w-0">
                    <Link 
                      href={`/profile/${userId}`}
                      className="block group"
                    >
                      <div className="text-lg font-semibold text-white group-hover:text-purple-300 transition-colors truncate">
                        {otherName ?? userId}
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        {userId && isUserOnline(userId) ? (
                          <span className="flex items-center gap-1 text-green-400">
                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                            在線
                          </span>
                        ) : (
                          <span className="text-gray-500">離線</span>
                        )}
                        <span className="text-gray-500">• 點擊查看個人頁面</span>
                      </div>
                    </Link>
                  </div>
                </div>
                
                {/* WebSocket 連線狀態 */}
                <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-700/50">
                  {isConnected ? (
                    <>
                      <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                      <span className="text-xs text-green-400 font-medium">即時連線</span>
                    </>
                  ) : (
                    <>
                      <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
                      <span className="text-xs text-yellow-400">連線中...</span>
                    </>
                  )}
                </div>
              </div>
            </motion.div>

            {/* 錯誤提示 */}
            <AnimatePresence>
              {error && (
                <motion.div 
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="mb-4 p-4 bg-red-600/20 border border-red-500/30 backdrop-blur-sm text-sm rounded-xl"
                >
                  <div className="flex items-center gap-2 text-red-400">
                    <span className="font-semibold">錯誤：</span>
                    {error}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* 訊息區域 */}
            <div className="relative">
              <div 
                ref={containerRef} 
                onScroll={onContainerScroll} 
                className="bg-gradient-to-br from-gray-800/40 to-gray-900/40 backdrop-blur-sm border border-gray-700/30 p-6 rounded-2xl mb-4 h-96 overflow-y-auto shadow-inner scroll-smooth"
                style={{
                  scrollbarWidth: 'thin',
                  scrollbarColor: '#4B5563 #1F2937'
                }}
              >
                {loading ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <div className="w-12 h-12 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto mb-3"></div>
                      <div className="text-gray-400">載入訊息中...</div>
                    </div>
                  </div>
                ) : messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-center">
                    <div>
                      <ChatBubbleLeftRightIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                      <div className="text-gray-400 mb-2">還沒有訊息</div>
                      <div className="text-sm text-gray-500">發送第一則訊息開始對話吧！</div>
                    </div>
                  </div>
                ) : (
                  <motion.div 
                    className="flex flex-col gap-3"
                    initial="hidden"
                    animate="visible"
                    variants={{
                      visible: { transition: { staggerChildren: 0.02 } }
                    }}
                  >
                    <AnimatePresence>
                      {messages.map((m, idx) => {
                        const isMe = m.sender_id === currentUserId;
                        const isLocal = String(m.id).startsWith('local-');
                        
                        return (
                          <motion.div
                            key={m.id}
                            ref={idx === messages.length - 1 ? lastMessageRef : undefined}
                            initial={{ opacity: 0, y: 20, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8 }}
                            transition={{ duration: 0.2 }}
                            className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}
                          >
                            <div className={`max-w-[75%] ${isMe ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
                              {/* 訊息氣泡 */}
                              <motion.div
                                whileHover={{ scale: 1.02 }}
                                className={`relative px-4 py-3 rounded-2xl shadow-md ${
                                  isMe 
                                    ? 'bg-gradient-to-br from-purple-600 to-pink-600 text-white rounded-br-sm' 
                                    : 'bg-gray-700/80 backdrop-blur-sm text-white rounded-bl-sm border border-gray-600/30'
                                }`}
                              >
                                <div className="text-sm leading-relaxed break-words whitespace-pre-wrap">
                                  {m.body}
                                </div>
                                
                                {/* 發送中指示器 */}
                                {isLocal && (
                                  <div className="absolute -right-1 -bottom-1 w-5 h-5 bg-yellow-500 rounded-full flex items-center justify-center animate-pulse">
                                    <div className="w-2 h-2 bg-white rounded-full"></div>
                                  </div>
                                )}
                              </motion.div>
                              
                              {/* 時間戳記與已讀狀態 */}
                              <div className={`flex items-center gap-1 px-1 ${isMe ? 'flex-row-reverse' : 'flex-row'}`}>
                                <span className="text-xs text-gray-500">
                                  {new Date(m.created_at || m.timestamp).toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })}
                                </span>
                                {isMe && !isLocal && m.read_at && (
                                  <CheckCircleIcon className="w-3.5 h-3.5 text-blue-400" title="已讀" />
                                )}
                                {isMe && !isLocal && !m.read_at && (
                                  <CheckIcon className="w-3.5 h-3.5 text-gray-500" title="已送達" />
                                )}
                              </div>
                            </div>
                          </motion.div>
                        );
                      })}
                    </AnimatePresence>
                  </motion.div>
                )}
              </div>

              {/* 新訊息浮動按鈕 */}
              <AnimatePresence>
                {newMessagesCount > 0 && !isAtBottomRef.current && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    className="absolute bottom-20 right-4"
                  >
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={async () => {
                        try {
                          isAtBottomRef.current = true;
                          scrollToBottomNow();
                          const lastId = messages.length ? messages[messages.length - 1].id : undefined;
                          if (lastId) {
                            const res = await Api.messages.markRead(userId as string, lastId).catch(() => null);
                            if (res) window.dispatchEvent(new CustomEvent('conversationsUpdated', { detail: res }));
                          }
                          setNewMessagesCount(0);
                        } catch (e) {}
                      }}
                      className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-full shadow-lg shadow-purple-500/30 font-medium"
                    >
                      <span>{newMessagesCount} 則新訊息</span>
                      <ArrowLeftIcon className="w-4 h-4 rotate-[-90deg]" />
                    </motion.button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* 輸入區域 */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-gradient-to-r from-gray-800/60 to-gray-700/60 backdrop-blur-md p-4 rounded-2xl border border-gray-600/30 shadow-lg"
            >
              <div className="flex gap-3">
                <textarea
                  ref={textareaRef}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  onKeyDown={(e) => {
                    if (sending) return;
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      send();
                    }
                  }}
                  placeholder="輸入訊息... (Enter 送出，Shift+Enter 換行)"
                  className="flex-1 p-3 rounded-xl bg-gray-900/50 border border-gray-600/30 focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 outline-none resize-none transition-all duration-300 text-white placeholder-gray-500"
                  rows={2}
                  style={{
                    scrollbarWidth: 'thin',
                    scrollbarColor: '#4B5563 #1F2937'
                  }}
                />
                <motion.button 
                  onClick={send} 
                  disabled={sending || !text.trim()}
                  whileHover={{ scale: sending ? 1 : 1.05 }}
                  whileTap={{ scale: sending ? 1 : 0.95 }}
                  className={`px-6 py-3 rounded-xl font-medium transition-all duration-300 flex items-center gap-2 ${
                    sending || !text.trim()
                      ? 'bg-gray-600 cursor-not-allowed opacity-50' 
                      : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 shadow-lg shadow-purple-500/30'
                  }`}
                >
                  {sending ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span className="hidden sm:inline">發送中</span>
                    </>
                  ) : (
                    <>
                      <PaperAirplaneIcon className="w-5 h-5" />
                      <span className="hidden sm:inline">送出</span>
                    </>
                  )}
                </motion.button>
              </div>
              <div className="mt-2 text-xs text-gray-500 flex items-center gap-1">
                <span>💡</span>
                <span>小提示：按 Enter 送出訊息，Shift+Enter 換行</span>
              </div>
            </motion.div>
          </>
        )}
      </div>
    </div>
  );
}

export default function MessagesPage() {
  return (
    <ErrorBoundary>
      <MessagesContent />
    </ErrorBoundary>
  );
}
