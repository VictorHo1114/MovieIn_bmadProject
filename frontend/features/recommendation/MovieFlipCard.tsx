"use client";

import { useState } from "react";
import { Star, Calendar, Zap, Film } from "lucide-react";
import type { RecommendedMovie } from "./services";

interface MovieFlipCardProps {
  movie: RecommendedMovie;
}

export function MovieFlipCard({ movie }: MovieFlipCardProps) {
  const [isFlipped, setIsFlipped] = useState(false);

  const posterUrl = movie.poster_url 
    ? `https://image.tmdb.org/t/p/w500${movie.poster_url}` 
    : '/placeholder-movie.jpg';

  return (
    <div className="perspective-1000 w-full h-[450px]">
      <div
        className={`relative w-full h-full transition-transform duration-700`}
        style={{
          transformStyle: "preserve-3d",
          transform: isFlipped ? "rotateY(180deg)" : "rotateY(0)",
        }}
      >
        {/* Front of card - Poster */}
        <div
          className="absolute w-full h-full rounded-2xl overflow-hidden 
                     border-2 border-purple-500/30 bg-black"
          style={{ backfaceVisibility: "hidden" }}
        >
          <div className="relative w-full h-full">
            {/* Poster Image */}
            <div className="absolute inset-0">
              <img
                src={posterUrl}
                alt={movie.title}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.currentTarget.src = '/placeholder-movie.jpg';
                }}
              />
            </div>

            {/* Gradient Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/60 to-transparent" />
            
            {/* Front Content */}
            <div className="relative h-full flex flex-col justify-end p-6">
              {/* Rating Badge */}
              <div className="absolute top-4 right-4 bg-black/80 rounded-full px-3 py-1
                            border border-yellow-500/50 flex items-center gap-1">
                <Star className="w-4 h-4 fill-yellow-500 text-yellow-500" />
                <span className="text-yellow-500 font-bold text-sm">
                  {movie.vote_average.toFixed(1)}
                </span>
              </div>

              {/* Title */}
              <h3 className="text-white text-2xl font-bold mb-2">
                {movie.title}
              </h3>

              {/* Year */}
              {movie.release_year && (
                <div className="flex items-center gap-2 text-gray-300 mb-4">
                  <Calendar className="w-4 h-4" />
                  <span>{movie.release_year}</span>
                </div>
              )}

              {/* Description Preview */}
              <p className="text-gray-300 text-sm mb-4 line-clamp-2">
                {movie.overview || "No description available"}
              </p>
              
              {/* Flip Button */}
              <button
                onClick={() => setIsFlipped(true)}
                className="mt-auto text-purple-400 text-sm hover:text-purple-300 
                         transition-colors flex items-center gap-2 self-start
                         bg-purple-500/20 px-4 py-2 rounded-full border border-purple-500/50"
              >
                <Zap className="w-4 h-4" />
                查看詳情
              </button>
            </div>
          </div>
        </div>

        {/* Back of card - Details */}
        <div
          className="absolute w-full h-full rounded-2xl overflow-hidden 
                     border-2 border-purple-500/50 bg-gradient-to-br 
                     from-gray-900 via-purple-900/30 to-gray-900"
          style={{
            backfaceVisibility: "hidden",
            transform: "rotateY(180deg)",
          }}
        >
          <div className="h-full flex flex-col p-6">
            {/* Header */}
            <div className="flex items-start gap-3 mb-6">
              <Film className="w-6 h-6 text-purple-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-purple-400 text-xl font-bold mb-1">
                  {movie.title}
                </h3>
                <p className="text-gray-400 text-sm">
                  {movie.release_year} • Rating: {movie.vote_average.toFixed(1)}/10
                </p>
              </div>
            </div>
            
            {/* Overview */}
            <div className="flex-1 overflow-y-auto mb-6">
              <h4 className="text-purple-300 font-semibold mb-2">Synopsis</h4>
              <p className="text-gray-300 text-sm leading-relaxed">
                {movie.overview || "No description available"}
              </p>

              {/* Match Scores */}
              {(movie.similarity_score || movie.feature_score) && (
                <div className="mt-4 pt-4 border-t border-purple-500/30">
                  <h4 className="text-purple-300 font-semibold mb-2">Match Info</h4>
                  <div className="space-y-2">
                    {movie.similarity_score !== undefined && (
                      <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 text-cyan-400" />
                        <span className="text-gray-300 text-sm">
                          Similarity: {(movie.similarity_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}
                    {movie.feature_score !== undefined && (
                      <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 text-purple-400" />
                        <span className="text-gray-300 text-sm">
                          Feature Match: {movie.feature_score.toFixed(0)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="grid grid-cols-2 gap-3">
              <button className="bg-purple-500 text-white px-4 py-2 rounded-lg 
                               hover:bg-purple-400 transition-colors font-medium">
                Watch Now
              </button>
              <button
                onClick={() => setIsFlipped(false)}
                className="border-2 border-purple-400 text-purple-400 px-4 py-2 rounded-lg 
                         hover:bg-purple-400/10 transition-colors font-medium"
              >
                Flip Back
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
