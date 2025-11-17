"use client";

import React from 'react';
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { API_BASE } from "@/lib/config";
import { postJSON } from '@/lib/http';
import { Api } from '@/lib/api';

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
  const [conversations, setConversations] = useState<any[] | null>(null);
  const [conversationsLoading, setConversationsLoading] = useState<boolean>(false);
  const [sending, setSending] = useState(false);
  const [newMessagesCount, setNewMessagesCount] = useState(0);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const isAtBottomRef = useRef<boolean>(true);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const pollingRef = useRef<number | null>(null);
  const convPollRef = useRef<number | null>(null);
  const lastMessageRef = useRef<HTMLDivElement | null>(null);
  const knownIdsRef = useRef<Set<string>>(new Set());
  const pausePollRef = useRef<boolean>(false);
  const isLoadingRef = useRef<boolean>(false); // prevent concurrent requests

  useEffect(() => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    setOtherName(null);
    // Try loading conversation from backend. Endpoint may not exist yet; that's ok.
    (async () => {
      try {
        const js = await Api.messages.getConversation(userId as string).catch((e) => { throw e; });
        // Api.messages.getConversation returns array or { items }
        const jsAny: any = js;
        const items: any[] = Array.isArray(jsAny) ? jsAny : (jsAny.items || jsAny || []);
        // keep only the most recent messages to avoid loading huge histories in the UI
        const recent = items.slice(-RECENT_LIMIT);
        setMessages(recent);
        // record known server-side ids so polling can decide what is truly new
        try {
          knownIdsRef.current = new Set(recent.filter((m: any) => !String(m.id).startsWith('local-')).map((m: any) => String(m.id)));
        } catch (e) {}
        // mark messages in this conversation as read (best-effort)
        (async () => {
          try {
            // determine last message id to reduce race (only mark up to what we've loaded)
            const lastId = items.length ? items[items.length - 1].id : undefined;
            const res = await Api.messages.markRead(userId as string, lastId);
            // fetch current unread_count to sync badge exactly
            let uc: any = null;
            try {
              uc = await Api.messages.unreadCount();
            } catch (err) {
              uc = null;
            }
            const detail = Object.assign({}, res || {}, { unreadCount: uc?.count });
            // notify other parts (NavBar, conversation list) to refresh
            window.dispatchEvent(new CustomEvent('conversationsUpdated', { detail }));
          } catch (e) {
            // ignore if unauthenticated or endpoint missing
          }
        })();
      } catch (e: any) {
        setError(String(e?.message ?? e));
        setMessages([]);
      } finally {
        setLoading(false);
      }
    })();

    // try load other user's display name if available
    (async () => {
      try {
        const p = await Api.profile.getById(userId as string);
        const name = p?.profile?.display_name || p?.email?.split('@')[0] || null;
        setOtherName(name);
      } catch (e) {
        // ignore
      }
    })();

    // start polling for new messages every 5s (reduced from 3s to reduce server load)
    if (pollingRef.current) {
      window.clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    pollingRef.current = window.setInterval(async () => {
      try {
        // Skip polling if paused, page not visible, or already loading
        if (pausePollRef.current || document.visibilityState !== 'visible' || isLoadingRef.current) return;
        isLoadingRef.current = true;
        const js = await Api.messages.getConversation(userId as string).catch(() => null);
        isLoadingRef.current = false;
        if (!js) return;
        const jsAny: any = js;
        const items: any[] = Array.isArray(jsAny) ? jsAny : (jsAny.items || jsAny || []);
        // merge new messages by id (append only unseen)
        setMessages((prev) => {
          const existing = new Set(prev.map((m) => String(m.id)));
          const toAdd = items.filter((it) => !existing.has(String(it.id)));
          // debug: log prev ids and incoming toAdd ids to diagnose duplicate/new-count issues
          try {
            // eslint-disable-next-line no-console
            console.debug('[messages.poll] prevIds=', Array.from(existing).slice(-10));
            // eslint-disable-next-line no-console
            console.debug('[messages.poll] toAddIds=', toAdd.map((t) => String(t.id)).slice(-10));
          } catch (e) {}
          if (toAdd.length === 0) return prev;

          // handle possible local optimistic messages: replace placeholders with server messages
          let merged = [...prev];
          for (const newMsg of toAdd) {
            const matchedIndex = merged.findIndex((m) => String(m.id).startsWith('local-') && m.body === newMsg.body);
            if (matchedIndex !== -1) {
              merged[matchedIndex] = newMsg;
            } else {
              merged.push(newMsg);
            }
          }
          // trim to RECENT_LIMIT
          if (merged.length > RECENT_LIMIT) merged = merged.slice(merged.length - RECENT_LIMIT);
          // dedupe by id (preserve first occurrence)
          const seen = new Set<string>();
          const deduped: any[] = [];
          for (const m of merged) {
            const idStr = String(m.id);
            if (seen.has(idStr)) continue;
            seen.add(idStr);
            deduped.push(m);
          }
          merged = deduped;
          // NOTE: do NOT update knownIdsRef here — keep previous known set until
          // we've computed uniqueAdded below. Updating early causes newly-merged
          // server ids to be considered "known" and prevents the unseen counter.
          // if window visible, mark up to latest id as read (best-effort)
          if (typeof document !== 'undefined' && document.visibilityState === 'visible') {
            try {
              const lastId = items.length ? items[items.length - 1].id : undefined;
                  if (lastId) {
                    // if user is at bottom, mark as read; otherwise increment "new messages" badge
                    if (isAtBottomRef.current) {
                              Api.messages.markRead(userId as string, lastId).then((res) => {
                                window.dispatchEvent(new CustomEvent('conversationsUpdated', { detail: res }));
                              }).catch(() => {});
                            } else {
                              // compute how many *unique* new ids were added relative to prev
                              // NOTE: if a server-provided message replaces a local optimistic placeholder
                              // (id starts with 'local-' and same body), do NOT count it as a new unseen message.
                              // use known server ids (persisted across polls) to determine true new server messages
                              const known = knownIdsRef.current || new Set<string>();
                              let uniqueAdded = 0;
                              const newlyKnown: string[] = [];
                              for (const m of toAdd) {
                                const idStr = String(m.id);
                                if (known.has(idStr)) continue;
                                // if we already have a local optimistic placeholder with same body, don't count as new
                                const hasLocalMatch = prev.some((p) => String(p.id).startsWith('local-') && p.body === m.body);
                                if (hasLocalMatch) continue;
                                uniqueAdded += 1;
                                newlyKnown.push(idStr);
                              }
                              if (newlyKnown.length > 0) {
                                try { for (const id of newlyKnown) knownIdsRef.current.add(id); } catch (e) {}
                              }
                              if (uniqueAdded > 0) {
                                // eslint-disable-next-line no-console
                                console.debug('[messages.poll] uniqueAdded=', uniqueAdded, 'prevCount=', newMessagesCount);
                                setNewMessagesCount((n) => n + uniqueAdded);
                              }
                            }
                  }
            } catch (e) {}
          }
          return merged;
        });
      } catch (e) {
        // ignore polling errors
        isLoadingRef.current = false;
      }
    }, 5000);

    return () => {
      if (pollingRef.current) {
        window.clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
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
        setConversations(items);
      } catch (e) {
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

    // polling fallback to keep list fresh (10s interval to reduce server load)
    if (convPollRef.current) {
      window.clearInterval(convPollRef.current);
      convPollRef.current = null;
    }
    convPollRef.current = window.setInterval(() => {
      // Only poll when page is visible
      if (document.visibilityState === 'visible') {
        loadConversations();
      }
    }, 10000);

    return () => {
      window.removeEventListener('conversationsUpdated', handleConvUpdated as EventListener);
      if (convPollRef.current) {
        window.clearInterval(convPollRef.current);
        convPollRef.current = null;
      }
    };
  }, [userId]);

  const send = async () => {
    if (!userId) return alert('請提供收件人 ID');
    if (!text.trim()) return;
    if (sending) return; // prevent duplicate sends
    setSending(true);
    try {
      // use postJSON which attaches Authorization header automatically when available
      const js: any = await postJSON('/messages', { recipient_id: userId, body: text });
      // js.item contains inserted row
      const inserted = js.item || js;
      // optimistic replacement with server-returned item if available
      if (inserted && inserted.id) {
        try { console.debug('[messages.send] server returned inserted id=', String(inserted.id)); } catch (e) {}
        setMessages((prev) => {
          const merged = [...prev, inserted];
          return merged.length > RECENT_LIMIT ? merged.slice(merged.length - RECENT_LIMIT) : merged;
        });
        // user just sent a message -> ensure we scroll to bottom and consider user at bottom
        try { isAtBottomRef.current = true; scrollToBottomNow(); pausePollRef.current = true; window.setTimeout(() => { pausePollRef.current = false; }, 1500); } catch (e) {}
      } else {
        const now = new Date().toISOString();
        try { console.debug('[messages.send] server did not return inserted id, creating local placeholder'); } catch (e) {}
        setMessages((prev) => {
          const merged = [...prev, { id: `local-${now}`, sender_id: currentUserId ?? 'me', recipient_id: userId, body: text, created_at: now }];
          return merged.length > RECENT_LIMIT ? merged.slice(merged.length - RECENT_LIMIT) : merged;
        });
        // user just sent a message -> ensure we scroll to bottom and consider user at bottom
        try { isAtBottomRef.current = true; scrollToBottomNow(); pausePollRef.current = true; window.setTimeout(() => { pausePollRef.current = false; }, 1500); } catch (e) {}
      }
      // notify other parts to refresh their conversation lists / unread counts
      try {
        window.dispatchEvent(new CustomEvent('conversationsUpdated', { detail: { sent: true } }));
      } catch (e) {}
      setText('');
    } catch (e: any) {
      const msg = String(e.message ?? e);
      if (msg.includes('[401]') || msg.toLowerCase().includes('not authenticated')) {
        alert('請先登入後再傳送私訊（未驗證）。');
        // optionally open login page
        return;
      }
      alert(`送出失敗：${msg}`);
    } finally {
      setSending(false);
      try { textareaRef.current?.focus(); } catch (e) {}
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">私訊</h1>
          <div className="flex gap-2">
            <Link href="/social/friends" className="px-3 py-2 bg-blue-600 rounded">好友</Link>
            <Link href="/profile" className="px-3 py-2 bg-gray-700 rounded">我的檔案</Link>
          </div>
        </div>

        {!userId ? (
          // show conversation list when no specific user is selected
          <div>
                {conversations === null && !conversationsLoading ? (
              <div className="bg-gray-800 p-6 rounded">請從好友列表或個人頁面點選「私訊」，或在網址列加上 `?user=&lt;user_id&gt;`。嘗試載入聊天室清單中…</div>
            ) : conversations && conversations.length === 0 ? (
              <div className="bg-gray-800 p-6 rounded">目前沒有聊天室。請先向好友發起私訊。</div>
            ) : (
              <div className="bg-gray-800 p-4 rounded">
                <div className="mb-3 flex items-center justify-between">
                  <div className="font-medium">聊天室</div>
                  <div className="text-sm text-gray-300 ml-2 w-20 text-right">
                    {conversationsLoading ? '載入中…' : ''}
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  {(conversations || []).map((c) => (
                    <Link key={c.user_id} href={`/messages?user=${c.user_id}`} className="p-3 bg-gray-700 rounded flex justify-between items-center hover:bg-gray-600">
                      <div>
                        <div className="font-medium">{c.display_name || c.user_id}</div>
                        <div className="text-sm text-gray-300">{c.last_message || '—'}</div>
                      </div>
                      {c.unread > 0 && (
                        <div className="inline-flex items-center justify-center px-2 py-0.5 text-xs font-semibold rounded-full bg-red-600 text-white">{c.unread}</div>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <>
            <div className="mb-4 text-sm text-gray-300">與使用者 <strong>{otherName ?? userId}</strong> 的對話頁面。</div>

            {error && (
              <div className="mb-4 p-3 bg-red-700 text-sm rounded">無法載入對話：{error}</div>
            )}

            <div ref={containerRef} onScroll={onContainerScroll} className="relative bg-gray-800 p-4 rounded mb-4 h-64 overflow-auto">
              {loading ? (
                <div>載入中…</div>
              ) : messages.length === 0 ? (
                <div className="text-gray-400">目前沒有訊息。</div>
              ) : (
                <div className="flex flex-col gap-3">
                  {messages.map((m, idx) => (
                    <div
                      key={m.id}
                      ref={idx === messages.length - 1 ? lastMessageRef : undefined}
                      className={`p-2 rounded ${m.sender_id === currentUserId ? 'bg-indigo-600 self-end' : 'bg-gray-700 self-start'}`}
                    >
                      <div className="text-sm">{m.body}</div>
                      <div className="text-xs text-gray-300 mt-1">{new Date(m.created_at).toLocaleString?.()}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
              {/* new messages floating indicator (shown when user scrolled up) */}
              {newMessagesCount > 0 && !isAtBottomRef.current && (
                <div className="absolute bottom-3 right-3">
                  <button
                    onClick={async () => {
                      try {
                        // scroll to bottom and mark as read up to last message
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
                    className="px-3 py-1 bg-indigo-600 text-white rounded shadow-lg text-sm"
                  >
                    新訊息 {newMessagesCount}，跳到底部
                  </button>
                </div>
              )}

            <div className="flex gap-2">
              <textarea
                ref={textareaRef}
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  // prevent sending while in-flight
                  if (sending) return;
                  // Enter to send, Shift+Enter for newline
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                placeholder="輸入訊息，按 Enter 送出，Shift+Enter 換行"
                className="flex-1 p-2 rounded bg-gray-800 border border-gray-700"
                rows={3}
              />
              <div className="flex flex-col gap-2">
                <button onClick={send} disabled={sending} aria-busy={sending} className={`px-4 py-2 rounded ${sending ? 'bg-green-400 cursor-wait' : 'bg-green-600'}`}>
                  {sending ? (
                    <span className="flex items-center gap-2">
                      <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" stroke="white" strokeOpacity="0.2" strokeWidth="4"/><path d="M22 12a10 10 0 00-10-10" stroke="white" strokeWidth="4" strokeLinecap="round"/></svg>
                      <span>傳送中</span>
                    </span>
                  ) : (
                    '送出'
                  )}
                </button>
              </div>
            </div>
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
