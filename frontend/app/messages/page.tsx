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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [otherName, setOtherName] = useState<string | null>(null);
  const [conversations, setConversations] = useState<any[] | null>(null);
  const [sending, setSending] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const pollingRef = useRef<number | null>(null);

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
        setMessages(items);
        // mark messages in this conversation as read (best-effort)
        (async () => {
          try {
            const res = await Api.messages.markRead(userId as string);
            // notify other parts (NavBar, conversation list) to refresh
            // include backend response (e.g. { marked: N }) for optimistic update
            window.dispatchEvent(new CustomEvent('conversationsUpdated', { detail: res }));
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

    // start polling for new messages every 3s
    if (pollingRef.current) {
      window.clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    pollingRef.current = window.setInterval(async () => {
      try {
        const js = await Api.messages.getConversation(userId as string).catch(() => null);
        if (!js) return;
        const jsAny: any = js;
        const items: any[] = Array.isArray(jsAny) ? jsAny : (jsAny.items || jsAny || []);
        // merge new messages by id (append only unseen)
        setMessages((prev) => {
          const existing = new Set(prev.map((m) => String(m.id)));
          const toAdd = items.filter((it) => !existing.has(String(it.id)));
          if (toAdd.length === 0) return prev;
          return [...prev, ...toAdd];
        });
      } catch (e) {
        // ignore polling errors
      }
    }, 3000);

    return () => {
      if (pollingRef.current) {
        window.clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [userId]);

  // scroll to bottom whenever messages change
  useEffect(() => {
    if (!containerRef.current) return;
    // small timeout to allow DOM update
    const t = window.setTimeout(() => {
      try {
        containerRef.current?.scrollTo({ top: containerRef.current.scrollHeight, behavior: 'smooth' });
      } catch (e) {}
    }, 80);
    return () => window.clearTimeout(t);
  }, [messages.length]);

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
    setConversations(null);
    (async () => {
      try {
        const js = await Api.messages.getConversations();
        const jsAny: any = js;
        const items: any[] = Array.isArray(jsAny) ? jsAny : (jsAny.items || jsAny || []);
        setConversations(items);
      } catch (e) {
        setConversations([]);
      }
    })();
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
        setMessages((prev) => [...prev, inserted]);
      } else {
        const now = new Date().toISOString();
        setMessages((prev) => [...prev, { id: `local-${now}`, sender_id: currentUserId ?? 'me', recipient_id: userId, body: text, created_at: now }]);
      }
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
            {conversations === null ? (
              <div className="bg-gray-800 p-6 rounded">請從好友列表或個人頁面點選「私訊」，或在網址列加上 `?user=&lt;user_id&gt;`。嘗試載入聊天室清單中…</div>
            ) : conversations.length === 0 ? (
              <div className="bg-gray-800 p-6 rounded">目前沒有聊天室。請先向好友發起私訊。</div>
            ) : (
              <div className="bg-gray-800 p-4 rounded">
                <div className="mb-3 font-medium">聊天室</div>
                <div className="flex flex-col gap-2">
                  {conversations.map((c) => (
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

            <div ref={containerRef} className="bg-gray-800 p-4 rounded mb-4 h-64 overflow-auto">
              {loading ? (
                <div>載入中…</div>
              ) : messages.length === 0 ? (
                <div className="text-gray-400">目前沒有訊息。</div>
              ) : (
                <div className="flex flex-col gap-3">
                  {messages.map((m) => (
                    <div key={m.id} className={`p-2 rounded ${m.sender_id === currentUserId ? 'bg-indigo-600 self-end' : 'bg-gray-700 self-start'}`}>
                      <div className="text-sm">{m.body}</div>
                      <div className="text-xs text-gray-300 mt-1">{new Date(m.created_at).toLocaleString?.()}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

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
