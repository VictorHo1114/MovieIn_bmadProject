"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { API_BASE } from "@/lib/config";

interface FriendCard {
  id: number | string;
  display_name: string;
  avatar_url?: string | null;
  level?: number;
  total_points?: number;
  bio?: string | null;
  favorite_genres?: string[];
  similarity_score?: number;
}

const MOCK: FriendCard[] = [
  {
    id: 101,
    display_name: "Alice Lin",
    avatar_url: "/img/default-avatar.jpg",
    level: 3,
    total_points: 450,
    bio: "最愛科幻與懸疑片",
    favorite_genres: ["科幻", "驚悚"],
    similarity_score: 72,
  },
  {
    id: 102,
    display_name: "Bob Chen",
    avatar_url: "/img/default-avatar.jpg",
    level: 4,
    total_points: 800,
    bio: "愛看經典與獨立電影",
    favorite_genres: ["劇情", "獨立"],
    similarity_score: 65,
  },
  {
    id: 103,
    display_name: "Emma Wu",
    avatar_url: "/img/default-avatar.jpg",
    level: 2,
    total_points: 150,
    bio: "新手影迷，剛開始建立 Top10",
    favorite_genres: ["愛情", "喜劇"],
    similarity_score: 58,
  },
];

export default function SocialPage() {
  const [people, setPeople] = useState<FriendCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const res = await fetch(`${API_BASE}/friends/suggested?limit=12`);
        if (!res.ok) throw new Error(`Status ${res.status}`);
        const data = await res.json();
        if (!mounted) return;
        setPeople(data.users ?? data.items ?? []);
      } catch (e: any) {
        console.warn("Failed to fetch suggested friends, using mock", e);
        if (!mounted) return;
        setPeople(MOCK);
        setError(null);
      } finally {
        if (!mounted) return;
        setLoading(false);
      }
    }
    load();
    return () => { mounted = false; };
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 px-4 py-8">
      <h1 className="text-3xl font-bold text-white mb-6 text-center">交友 — 推薦好友</h1>

      {loading ? (
        <div className="text-white text-center">載入中...</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">
          {people.map((p) => (
            <Link key={p.id} href={`/profile/${p.id}`} className="group">
              <article className="bg-gray-800 rounded-2xl overflow-hidden shadow-xl hover:shadow-yellow-400/40 transition-all duration-300 hover:-translate-y-1 border border-gray-700">
                <div className="relative aspect-[2/3]">
                  <img src={p.avatar_url ?? '/img/default-avatar.jpg'} alt={p.display_name} className="w-full h-full object-cover" />
                  <div className="absolute top-2 right-2 px-2 py-1 bg-yellow-400 text-gray-900 text-sm font-bold rounded shadow">
                    {p.similarity_score ? `💚 ${p.similarity_score}%` : `LV ${p.level ?? 1}`}
                  </div>
                </div>
                <div className="p-4">
                  <h2 className="text-white font-bold text-lg mb-1 group-hover:text-yellow-300 line-clamp-1">{p.display_name}</h2>
                  <div className="text-sm text-gray-300 mb-2">等級 {p.level ?? 'N/A'} • {p.total_points ?? 0} 分</div>
                  {p.bio && <p className="text-sm text-gray-200 line-clamp-3">{p.bio}</p>}
                </div>
              </article>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
