// app/search/page.tsx
"use client";

import { SlideUpTransition } from "@/components/PageTransition";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { searchMovies } from "@/features/search/services";

export default function Page() {
  const searchParams = useSearchParams();
  const q = searchParams.get("q") ?? "";
  const [data, setData] = useState<any>({ items: [] });

  useEffect(() => {
    if (q) {
      searchMovies(q).then(setData);
    }
  }, [q]);

  return (
    <SlideUpTransition>
      <div className="min-h-screen p-8">
        <h1 className="text-3xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          Search Results
        </h1>
        {q && (
          <p className="text-gray-400 mb-4">搜尋關鍵字: <span className="text-white font-semibold">{q}</span></p>
        )}
        <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
          <pre className="text-sm text-gray-300">{JSON.stringify(data, null, 2)}</pre>
        </div>
      </div>
    </SlideUpTransition>
  );
}