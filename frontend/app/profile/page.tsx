// app/profile/page.tsx
"use client";

import { SlideUpTransition } from "@/components/PageTransition";
import { useEffect, useState } from "react";
import { getMyProfile } from "@/features/profile/services";

export default function Page() {
  const [profile, setProfile] = useState<any>(null);
  
  useEffect(() => {
    getMyProfile().then(setProfile);
  }, []);

  return (
    <SlideUpTransition>
      <div className="min-h-screen p-8">
        <h1 className="text-3xl font-bold mb-6 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
          Profile
        </h1>
        <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
          <pre className="text-sm text-gray-300">{JSON.stringify(profile, null, 2)}</pre>
        </div>
      </div>
    </SlideUpTransition>
  );
}