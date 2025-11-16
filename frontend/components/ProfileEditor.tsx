"use client";

import React, { useEffect, useState } from "react";
import { Api } from "../lib/api";

type Props = {
  userId: string;
};

export default function ProfileEditor({ userId }: Props) {
  const [isOwner, setIsOwner] = useState(false);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<any>({
    display_name: "",
    avatar_url: "",
    bio: "",
    favorite_genres: "",
    locale: "",
    adult_content_opt_in: false,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const me = await Api.profile.me();
        if (!mounted) return;
        if (me && (me.user_id as string) === userId) {
          setIsOwner(true);
          // prefill with server profile if available
          const p: any = me.profile || {};
          setForm({
            display_name: p.display_name || me.email || "", 
            avatar_url: p.avatar_url || "",
            bio: p.bio || "",
            favorite_genres: Array.isArray(p.favorite_genres) ? p.favorite_genres.join(", ") : (p.favorite_genres || ""),
            locale: p.locale || "",
            adult_content_opt_in: !!p.adult_content_opt_in,
          });
        }
      } catch (e) {
        // not logged in or no access
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false };
  }, [userId]);

  if (loading || !isOwner) return null;

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = {
        display_name: form.display_name || null,
        avatar_url: form.avatar_url || null,
        bio: form.bio || null,
        favorite_genres: form.favorite_genres ? form.favorite_genres.split(",").map((s: string) => s.trim()).filter(Boolean) : [],
        locale: form.locale || null,
        adult_content_opt_in: !!form.adult_content_opt_in,
      };
      await Api.profile.updateMe(payload as any);
      // refresh the page to reflect server-side changes
      window.location.reload();
    } catch (err: any) {
      setError(err?.message || "更新失敗");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mt-3">
      {!editing ? (
        <button
          onClick={() => setEditing(true)}
          className="inline-flex items-center px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700"
        >
          編輯個人資料
        </button>
      ) : (
        <form onSubmit={onSave} className="bg-white p-4 rounded shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium">顯示名稱</label>
              <input value={form.display_name} onChange={e => setForm({...form, display_name: e.target.value})} className="mt-1 block w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="text-sm font-medium">頭像 URL</label>
              <input value={form.avatar_url} onChange={e => setForm({...form, avatar_url: e.target.value})} className="mt-1 block w-full border rounded px-2 py-1" />
            </div>
            <div className="md:col-span-2">
              <label className="text-sm font-medium">自我介紹 (bio)</label>
              <textarea value={form.bio} onChange={e => setForm({...form, bio: e.target.value})} rows={4} className="mt-1 block w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="text-sm font-medium">喜愛的類型 (逗號分隔)</label>
              <input value={form.favorite_genres} onChange={e => setForm({...form, favorite_genres: e.target.value})} className="mt-1 block w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="text-sm font-medium">語言 (locale)</label>
              <input value={form.locale} onChange={e => setForm({...form, locale: e.target.value})} className="mt-1 block w-full border rounded px-2 py-1" />
            </div>
            <div className="flex items-center gap-2">
              <input id="adult" type="checkbox" checked={form.adult_content_opt_in} onChange={e=>setForm({...form, adult_content_opt_in: e.target.checked})} />
              <label htmlFor="adult" className="text-sm">成人內容顯示 (opt-in)</label>
            </div>
          </div>
          <div className="mt-3 flex gap-2">
            <button type="submit" disabled={saving} className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">{saving? '儲存中...' : '儲存'}</button>
            <button type="button" onClick={()=>setEditing(false)} className="px-3 py-1 border rounded">取消</button>
            {error ? <div className="text-sm text-red-600">{error}</div> : null}
          </div>
        </form>
      )}
    </div>
  );
}
