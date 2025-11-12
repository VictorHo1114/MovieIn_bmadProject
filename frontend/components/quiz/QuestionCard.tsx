'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import type { DailyQuiz } from '@/lib/api';

interface QuestionCardProps {
  quiz: DailyQuiz;
  index: number;
  onSubmit: (answer: number) => void;
  result?: {
    is_correct: boolean;
    points_earned: number;
    explanation: string | null;
  } | null;
  isFlipped: boolean;
  isFirstRound: boolean;
  disabled?: boolean;
}

const DIFFICULTY_CONFIG = {
  easy: { label: '簡單', icon: '⭐', color: 'from-green-400 to-emerald-500' },
  medium: { label: '中等', icon: '⭐⭐', color: 'from-yellow-400 to-orange-500' },
  hard: { label: '困難', icon: '⭐⭐⭐', color: 'from-red-400 to-pink-500' },
};

export function QuestionCard({ 
  quiz, 
  index, 
  onSubmit, 
  result, 
  isFlipped, 
  isFirstRound,
  disabled 
}: QuestionCardProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const difficultyConfig = DIFFICULTY_CONFIG[quiz.difficulty as keyof typeof DIFFICULTY_CONFIG];

  // Reset selected answer when card flips back to front
  useEffect(() => {
    if (!isFlipped) {
      setSelectedAnswer(null);
    }
  }, [isFlipped]);

  const handleSubmit = () => {
    if (selectedAnswer !== null && !disabled) {
      onSubmit(selectedAnswer);
    }
  };

  return (
    <div className="perspective-1000 h-[500px]">
      <motion.div
        className="relative w-full h-full"
        animate={{ rotateY: isFlipped ? 180 : 0 }}
        transition={{ duration: 0.6, type: "spring", stiffness: 100 }}
        style={{ transformStyle: "preserve-3d" }}
      >
        {/* Front - Question */}
        <div
          className="absolute w-full h-full backface-hidden"
          style={{ backfaceVisibility: "hidden" }}
        >
          <div className="h-full bg-gradient-to-br from-gray-900/95 to-gray-800/95 backdrop-blur-sm border-2 border-gray-700 rounded-2xl p-5 shadow-2xl flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <span className="text-lg">🎬</span>
                <span className="text-xs">{quiz.category || '電影知識'}</span>
              </div>
              <div className={`px-2.5 py-1 rounded-full bg-gradient-to-r ${difficultyConfig.color} text-white text-xs font-semibold`}>
                {difficultyConfig.icon}
              </div>
            </div>

            {/* Question Number */}
            <div className="text-center mb-3">
              <span className="text-purple-400 text-3xl font-bold">#{index + 1}</span>
            </div>

            {/* Question */}
            <div className="flex-1 flex items-center justify-center mb-4">
              <p className="text-white text-base leading-relaxed font-medium text-center px-2">
                {quiz.question}
              </p>
            </div>

            {/* Options */}
            <div className="space-y-2 mb-3">
              {quiz.options.map((option, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedAnswer(idx)}
                  disabled={disabled}
                  className={`w-full text-left px-3 py-2.5 rounded-lg transition-all duration-200 ${
                    selectedAnswer === idx
                      ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white border-2 border-purple-400 shadow-lg shadow-purple-500/30'
                      : 'bg-gray-800/50 text-gray-300 border border-gray-700 hover:border-purple-500/50 hover:bg-gray-800/70'
                  } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <span className="font-bold mr-2 text-sm">{String.fromCharCode(65 + idx)}.</span>
                  <span className="text-sm">{option}</span>
                </button>
              ))}
            </div>

            {/* Submit Button */}
            <button
              onClick={handleSubmit}
              disabled={selectedAnswer === null || disabled}
              className={`w-full py-2.5 rounded-lg font-bold text-sm transition-all ${
                selectedAnswer !== null && !disabled
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:shadow-lg hover:shadow-purple-500/50'
                  : 'bg-gray-700 text-gray-500 cursor-not-allowed'
              }`}
            >
              提交答案
            </button>
          </div>
        </div>

        {/* Back - Result */}
        <div
          className="absolute w-full h-full backface-hidden"
          style={{ 
            backfaceVisibility: "hidden",
            transform: "rotateY(180deg)"
          }}
        >
          <div className="h-full bg-gradient-to-br from-gray-900/95 to-gray-800/95 backdrop-blur-sm border-2 border-gray-700 rounded-2xl p-4 shadow-2xl flex flex-col overflow-hidden">
            {/* Movie Poster */}
            {quiz.movie_reference && (
              <div className="flex flex-col items-center mb-3">
                <div className="w-36 h-52 bg-gray-800 rounded-lg border-2 border-gray-700 shadow-lg overflow-hidden">
                  {quiz.movie_reference.poster_url ? (
                    <img 
                      src={quiz.movie_reference.poster_url} 
                      alt={quiz.movie_reference.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <span className="text-4xl">🎬</span>
                    </div>
                  )}
                </div>
                <p className="text-purple-400 font-bold text-sm text-center leading-tight mt-1.5">{quiz.movie_reference.title}</p>
                <p className="text-gray-500 text-xs">({quiz.movie_reference.year})</p>
              </div>
            )}

            {/* Result Status - Compact */}
            <div className={`text-center py-2 rounded-lg mb-2.5 ${
              result?.is_correct 
                ? 'bg-gradient-to-br from-green-900/40 to-emerald-900/40 border border-green-500/60' 
                : 'bg-gradient-to-br from-red-900/40 to-rose-900/40 border border-red-500/60'
            }`}>
              <div className="flex items-center justify-center gap-2">
                <span className="text-xl">{result?.is_correct ? '✅' : '❌'}</span>
                <span className={`text-sm font-bold ${result?.is_correct ? 'text-green-300' : 'text-red-300'}`}>
                  {result?.is_correct ? '答對了！' : '答錯了'}
                </span>
                {result?.is_correct && result.points_earned > 0 && (
                  <span className="bg-yellow-500/20 border border-yellow-500/50 px-2 py-0.5 rounded text-yellow-300 font-bold text-xs">
                    +{result.points_earned}分
                  </span>
                )}
              </div>
              {!isFirstRound && (
                <div className="mt-0.5 text-blue-300 text-xs">🔁 練習模式</div>
              )}
            </div>

            {/* Correct Answer */}
            <div className="bg-gray-900/50 rounded-lg p-2.5 mb-2.5">
              <p className="text-gray-400 text-xs mb-0.5">✓ 正確答案：</p>
              <p className="text-white font-semibold text-xs leading-tight">
                {String.fromCharCode(65 + (quiz.correct_answer ?? 0))}. {quiz.options[quiz.correct_answer ?? 0]}
              </p>
            </div>

            {/* Explanation */}
            {quiz.explanation && (
              <div className="bg-blue-900/20 rounded-lg p-2 border border-blue-500/30">
                <p className="text-blue-200 text-xs font-semibold mb-0.5">💡 詳解</p>
                <div className="text-blue-300 text-xs leading-tight overflow-hidden" style={{ display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical' }}>
                  {quiz.explanation}
                </div>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
