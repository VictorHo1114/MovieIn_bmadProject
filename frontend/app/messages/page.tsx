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
  const containerRef = useRef<HTMLDivElement | null>(null);
  const pollingRef = useRef<number | null>(null);

  useEffect(() => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    // Try loading conversation from backend. Endpoint may not exist yet; that's ok.
    (async () => {
      try {
        const res = await fetch(`${API_BASE.replace(/\/$/, '')}/messages/conversation?user=${encodeURIComponent(userId)}`);
        if (!res.ok) {
          // show friendly message; don't throw so UI remains usable
          setError(`伺服器回應 ${res.status} ${res.statusText}`);
          setMessages([]);
        } else {
          const js = await res.json();
          setMessages(js.items || js || []);
        }
      } catch (e: any) {
        setError(String(e.message ?? e));
      } finally {
        setLoading(false);
      }
    })();

    // start polling for new messages every 3s
    if (pollingRef.current) {
      window.clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    pollingRef.current = window.setInterval(async () => {
      try {
        const r = await fetch(`${API_BASE.replace(/\/$/, '')}/messages/conversation?user=${encodeURIComponent(userId)}`);
        if (!r.ok) return;
        const js = await r.json();
        const items: any[] = js.items || js || [];
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

  const send = async () => {
    if (!userId) return alert('請提供收件人 ID');
    if (!text.trim()) return;
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
          <div className="bg-gray-800 p-6 rounded">請從好友列表或個人頁面點選「私訊」，或在網址列加上 `?user=&lt;user_id&gt;`。</div>
        ) : (
          <>
            <div className="mb-4 text-sm text-gray-300">與使用者 <strong>{userId}</strong> 的對話頁面。</div>

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
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
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
                <button onClick={send} className="px-4 py-2 bg-green-600 rounded">送出</button>
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
