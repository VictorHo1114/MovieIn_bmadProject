"use client";

import { useState, useEffect, useRef } from "react";
import { ChevronDown, X } from "lucide-react";

interface FilterControlsProps {
  selectedEras: string[];
  selectedGenres: string[];
  onErasChange: (eras: string[]) => void;
  onGenresChange: (genres: string[]) => void;
  gap?: string;  // 🆕 可選的 gap 參數
}

// 年代選項 - 從 backend mapping_tables.py
const ERA_OPTIONS = [
  { id: "60s", label: "60 年代", range: [1960, 1969] },
  { id: "70s", label: "70 年代", range: [1970, 1979] },
  { id: "80s", label: "80 年代", range: [1980, 1989] },
  { id: "90s", label: "90 年代", range: [1990, 1999] },
  { id: "00s", label: "00 年代", range: [2000, 2009] },
  { id: "10s", label: "10 年代", range: [2010, 2019] },
  { id: "20s", label: "20 年代", range: [2020, 2029] },
];

// 類型選項 - 19 個類型（繁體中文）
const GENRE_OPTIONS = [
  "動作", "冒險", "動畫", "喜劇", "犯罪",
  "紀錄片", "劇情", "家庭", "奇幻", "歷史",
  "恐怖", "音樂", "懸疑", "愛情", "科幻",
  "電視電影", "驚悚", "戰爭", "西部"
];

export function FilterControls({
  selectedEras,
  selectedGenres,
  onErasChange,
  onGenresChange,
  gap = "8px"  // 🆕 預設值 8px
}: FilterControlsProps) {
  const [isEraOpen, setIsEraOpen] = useState(false);
  const [isGenreOpen, setIsGenreOpen] = useState(false);
  const eraRef = useRef<HTMLDivElement>(null);
  const genreRef = useRef<HTMLDivElement>(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (eraRef.current && !eraRef.current.contains(event.target as Node)) {
        setIsEraOpen(false);
      }
      if (genreRef.current && !genreRef.current.contains(event.target as Node)) {
        setIsGenreOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  const toggleEra = (eraId: string) => {
    if (selectedEras.includes(eraId)) {
      onErasChange(selectedEras.filter(e => e !== eraId));
    } else {
      // 最多選 3 個
      if (selectedEras.length < 3) {
        onErasChange([...selectedEras, eraId]);
      }
    }
  };

  const toggleGenre = (genre: string) => {
    if (selectedGenres.includes(genre)) {
      onGenresChange(selectedGenres.filter(g => g !== genre));
    } else {
      // 最多選 3 個
      if (selectedGenres.length < 3) {
        onGenresChange([...selectedGenres, genre]);
      }
    }
  };

  const removeEra = (eraId: string) => {
    onErasChange(selectedEras.filter(e => e !== eraId));
  };

  const removeGenre = (genre: string) => {
    onGenresChange(selectedGenres.filter(g => g !== genre));
  };

  return (
    <div className="w-full grid grid-cols-2 gap-2">
      {/* 年代選擇器 - 下拉式 */}
      <div className="relative" ref={eraRef}>
        <div 
          onClick={() => setIsEraOpen(!isEraOpen)}
          className="min-h-[32px] px-2.5 py-1 bg-black/80 border border-white/30 
                   rounded-md cursor-pointer hover:border-white/60 hover:shadow-[0_0_10px_rgba(255,255,255,0.2)]
                   transition-all backdrop-blur-sm
                   flex flex-wrap gap-1 items-center text-xs"
        >
          {selectedEras.length === 0 ? (
            <span className="text-gray-500 text-xs">年代 0/3</span>
          ) : (
            <>
              <span className="text-white/90 text-xs">年代 {selectedEras.length}/3:</span>
              {selectedEras.map(eraId => {
                const era = ERA_OPTIONS.find(e => e.id === eraId);
                return (
                  <span
                    key={eraId}
                    className="inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-white/80 
                             text-black text-xs rounded-full shadow-sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeEra(eraId);
                    }}
                  >
                    {era?.label}
                    <X className="w-2.5 h-2.5" />
                  </span>
                );
              })}
            </>
          )}
          <ChevronDown className={`w-3 h-3 text-gray-400 ml-auto transition-transform ${isEraOpen ? 'rotate-180' : ''}`} />
        </div>

        {/* Dropdown Options */}
        {isEraOpen && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-black/95 border border-white/30 
                        rounded-md shadow-xl z-50 max-h-40 overflow-y-auto backdrop-blur-md">
            {ERA_OPTIONS.map(era => {
              const isSelected = selectedEras.includes(era.id);
              const isDisabled = !isSelected && selectedEras.length >= 3;
              return (
                <button
                  key={era.id}
                  onClick={() => !isDisabled && toggleEra(era.id)}
                  disabled={isDisabled}
                  className={`w-full px-2.5 py-1 text-left text-xs transition-colors
                    ${isSelected 
                      ? 'bg-white/20 text-white' 
                      : 'text-gray-400 hover:bg-white/10'
                    }
                    ${isDisabled ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer'}
                  `}
                >
                  {era.label}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* 類型選擇器 - 下拉式 */}
      <div className="relative" ref={genreRef}>
        <div 
          onClick={() => setIsGenreOpen(!isGenreOpen)}
          className="min-h-[32px] px-2.5 py-1 bg-black/80 border border-white/30 
                   rounded-md cursor-pointer hover:border-white/60 hover:shadow-[0_0_10px_rgba(255,255,255,0.2)]
                   transition-all backdrop-blur-sm
                   flex flex-wrap gap-1 items-center text-xs"
        >
          {selectedGenres.length === 0 ? (
            <span className="text-gray-500 text-xs">類型 0/3</span>
          ) : (
            <>
              <span className="text-white/90 text-xs">類型 {selectedGenres.length}/3:</span>
              {selectedGenres.map(genre => (
                <span
                  key={genre}
                  className="inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-white/80 
                           text-black text-xs rounded-full shadow-sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeGenre(genre);
                  }}
                >
                  {genre}
                  <X className="w-2.5 h-2.5" />
                </span>
              ))}
            </>
          )}
          <ChevronDown className={`w-3 h-3 text-gray-400 ml-auto transition-transform ${isGenreOpen ? 'rotate-180' : ''}`} />
        </div>

        {/* Dropdown Options */}
        {isGenreOpen && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-black/95 border border-white/30 
                        rounded-md shadow-xl z-50 max-h-40 overflow-y-auto backdrop-blur-md">
            {GENRE_OPTIONS.map(genre => {
              const isSelected = selectedGenres.includes(genre);
              const isDisabled = !isSelected && selectedGenres.length >= 3;
              return (
                <button
                  key={genre}
                  onClick={() => !isDisabled && toggleGenre(genre)}
                  disabled={isDisabled}
                  className={`w-full px-2.5 py-1 text-left text-xs transition-colors
                    ${isSelected 
                      ? 'bg-white/20 text-white' 
                      : 'text-gray-400 hover:bg-white/10'
                    }
                    ${isDisabled ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer'}
                  `}
                >
                  {genre}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
