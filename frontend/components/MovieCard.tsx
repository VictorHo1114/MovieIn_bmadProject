// components/MovieCard.tsx
"use client";

import type { RecommendedMovie } from "@/features/recommendation/services";
import Image from "next/image";
import { useState } from "react";

interface MovieCardProps {
  movie: RecommendedMovie;
}

export function MovieCard({ movie }: MovieCardProps) {
  const [isFlipped, setIsFlipped] = useState(false);
  const posterUrl = movie.poster_url || "/placeholder-movie.png";
  const rating = movie.vote_average.toFixed(1);

  return (
    <div className="relative h-[450px] w-full perspective-1000">
      <div 
        className={`relative w-full h-full transition-transform duration-700 transform-style-3d ${
          isFlipped ? 'rotate-y-180' : ''
        }`}
        style={{ transformStyle: 'preserve-3d' }}
      >
        {/* 正面 - Front Side */}
        <div 
          className="absolute inset-0 backface-hidden"
          style={{ backfaceVisibility: 'hidden' }}
        >
          <div className="group relative overflow-hidden rounded-lg border border-gray-700 bg-gray-800/50 h-full transition-all duration-300 hover:shadow-xl hover:shadow-purple-500/20">
            {/* Poster Image */}
            <div className="relative aspect-[2/3] w-full overflow-hidden bg-gray-900">
              <Image
                src={posterUrl}
                alt={movie.title}
                fill
                className="object-cover"
                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.src = "/placeholder-movie.png";
                }}
              />
              
              {/* Rating Badge */}
              <div className="absolute top-2 right-2 bg-black/80 backdrop-blur-sm rounded-full px-2 py-1">
                <span className="text-yellow-400 font-bold text-sm">★ {rating}</span>
              </div>

              {/* Flip Button */}
              <button
                onClick={() => setIsFlipped(true)}
                className="absolute bottom-2 right-2 bg-purple-600 hover:bg-purple-700 text-white rounded-full p-2 transition-all duration-300 opacity-0 group-hover:opacity-100"
                aria-label="Flip card"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                </svg>
              </button>
            </div>

            {/* Movie Title (正面只顯示標題) */}
            <div className="p-4">
              <h3 className="font-bold text-lg line-clamp-2 group-hover:text-purple-400 transition-colors">
                {movie.title}
              </h3>
              {movie.release_year && (
                <p className="text-sm text-gray-400 mt-1">{movie.release_year}</p>
              )}
            </div>
          </div>
        </div>

        {/* 背面 - Back Side */}
        <div 
          className="absolute inset-0 backface-hidden rotate-y-180"
          style={{ 
            backfaceVisibility: 'hidden',
            transform: 'rotateY(180deg)'
          }}
        >
          <div className="relative overflow-hidden rounded-lg border border-gray-700 bg-gradient-to-br from-gray-800 to-gray-900 h-full p-4 flex flex-col">
            {/* Close/Flip Back Button */}
            <button
              onClick={() => setIsFlipped(false)}
              className="absolute top-2 right-2 bg-gray-700 hover:bg-gray-600 text-white rounded-full p-1.5 transition-all z-10"
              aria-label="Flip back"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>

            {/* 電影標題 */}
            <h3 className="font-bold text-xl mb-3 pr-8 text-purple-400">
              {movie.title}
            </h3>

            {/* 電影簡介 */}
            <div className="flex-1 overflow-y-auto space-y-3 text-sm
                          scrollbar-thin scrollbar-track-transparent 
                          scrollbar-thumb-white/20 hover:scrollbar-thumb-white/40
                          [&::-webkit-scrollbar]:w-1.5
                          [&::-webkit-scrollbar-track]:bg-transparent
                          [&::-webkit-scrollbar-thumb]:bg-white/20
                          [&::-webkit-scrollbar-thumb]:rounded-full
                          [&::-webkit-scrollbar-thumb:hover]:bg-white/40">
              <div>
                <h4 className="font-semibold text-gray-300 mb-1">📝 簡介</h4>
                <p className="text-gray-400 text-xs leading-relaxed">
                  {movie.overview || "暫無簡介"}
                </p>
              </div>
            </div>

            {/* 底部按鈕區 */}
            <div className="mt-3 pt-3 border-t border-gray-700 space-y-2">
              <button 
                className="w-full bg-purple-600 hover:bg-purple-700 text-white text-sm py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
                onClick={() => console.log('Add to watchlist:', movie.id)}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                  <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                </svg>
                加入 Watchlist
              </button>
              
              <button 
                className="w-full bg-yellow-600 hover:bg-yellow-700 text-white text-sm py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
                onClick={() => console.log('Add to top 10:', movie.id)}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                加入 Top 10 List
              </button>
            </div>

            {/* 評分顯示 */}
            <div className="mt-2 text-center">
              <span className="text-yellow-400 font-bold text-sm">★ {rating}</span>
              <span className="text-gray-500 text-xs ml-1">/ 10</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}