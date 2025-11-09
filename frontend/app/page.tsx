"use client";

import { FadeInTransition } from "@/components/PageTransition";

export default function Index() {
  return (
    <FadeInTransition>
      <div className="flex flex-col items-center justify-center min-h-screen">
        <h1 className="text-4xl font-bold mb-4">Welcome to MovieIN</h1>
        <p className="text-gray-400">首頁內容等待合併...</p>
      </div>
    </FadeInTransition>
  );
}