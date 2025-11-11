'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Api, type TodayQuizResponse } from '@/lib/api';
import { useRouter } from 'next/navigation';

const DIFFICULTY_CONFIG = {
  easy: { label: '簡單', icon: '⭐', color: 'from-green-400 to-emerald-500' },
  medium: { label: '中等', icon: '⭐⭐', color: 'from-yellow-400 to-orange-500' },
  hard: { label: '困難', icon: '⭐⭐⭐', color: 'from-red-400 to-pink-500' },
};

export function HomeQuizWidget() {
  const [quizData, setQuizData] = useState<TodayQuizResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const router = useRouter();

  useEffect(() => {
    fetchTodayQuiz();
  }, []);

  const fetchTodayQuiz = async () => {
    try {
      setIsLoading(true);
      const data = await Api.quiz.getToday();
      setQuizData(data);
      setShowResult(data.has_answered);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch quiz:', err);
      setError('載入失敗');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!quizData?.quiz || selectedAnswer === null || isSubmitting) return;

    try {
      setIsSubmitting(true);
      const result = await Api.quiz.submit({
        quiz_id: quizData.quiz.id,
        answer: selectedAnswer,
        time_spent: 15,
      });

      // Update quiz data with result
      setQuizData({
        ...quizData,
        has_answered: true,
        daily_attempts: quizData.daily_attempts + 1,
        remaining_attempts: quizData.remaining_attempts - 1,
        user_attempt: {
          id: 0,
          quiz_id: quizData.quiz.id,
          user_answer: selectedAnswer,
          is_correct: result.is_correct,
          points_earned: result.points_earned,
          time_spent: 15,
          answered_at: new Date().toISOString(),
        },
      });
      setShowResult(true);

      // 廣播積分更新事件，讓 Profile 頁面重新載入資料
      if (result.is_correct) {
        window.dispatchEvent(new CustomEvent('quizPointsUpdated'));
      }
    } catch (err: any) {
      console.error('Failed to submit answer:', err);
      alert('提交失敗，請稍後再試');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNextQuiz = async () => {
    setSelectedAnswer(null);
    setShowResult(false);
    await fetchTodayQuiz();
  };

  if (isLoading) {
    return (
      <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6">
        <div className="flex items-center justify-center py-8">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full"
          />
        </div>
      </div>
    );
  }

  if (error || !quizData?.quiz) {
    return null; // 沒有題目時不顯示
  }

  const { quiz, user_attempt, has_answered } = quizData;
  const difficultyConfig = DIFFICULTY_CONFIG[quiz.difficulty as keyof typeof DIFFICULTY_CONFIG];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-sm border border-gray-700 rounded-2xl p-6 shadow-2xl"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🎬</span>
          <div>
            <h3 className="text-xl font-bold text-white">每日電影問答</h3>
            <p className="text-sm text-gray-400">
              {quiz.category || '電影知識'} • {quizData.daily_attempts}/{quizData.daily_limit} 已完成
            </p>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full bg-gradient-to-r ${difficultyConfig.color} text-white text-sm font-semibold`}>
          {difficultyConfig.icon} {difficultyConfig.label}
        </div>
      </div>

      {/* Question */}
      <div className="bg-gray-800/50 rounded-xl p-4 mb-4">
        <p className="text-white text-lg leading-relaxed">{quiz.question}</p>
      </div>

      {/* Options or Result */}
      <AnimatePresence mode="wait">
        {!showResult ? (
          <motion.div
            key="options"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-3 mb-4"
          >
            {quiz.options.map((option, index) => (
              <button
                key={index}
                onClick={() => setSelectedAnswer(index)}
                disabled={isSubmitting}
                className={`w-full text-left px-4 py-3 rounded-lg transition-all ${
                  selectedAnswer === index
                    ? 'bg-purple-600 text-white border-2 border-purple-400'
                    : 'bg-gray-800/50 text-gray-300 border-2 border-gray-700 hover:border-purple-500'
                }`}
              >
                <span className="font-semibold mr-2">{String.fromCharCode(65 + index)}.</span>
                {option}
              </button>
            ))}
          </motion.div>
        ) : (
          <motion.div
            key="result"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-4"
          >
            <div className={`rounded-xl p-4 ${user_attempt?.is_correct ? 'bg-green-900/30 border-2 border-green-500' : 'bg-red-900/30 border-2 border-red-500'}`}>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-2xl">{user_attempt?.is_correct ? '✅' : '❌'}</span>
                <span className="text-white font-bold text-lg">
                  {user_attempt?.is_correct ? '答對了！' : '答錯了'}
                </span>
              </div>
              <p className="text-gray-300 text-sm">
                正確答案：<span className="font-semibold">{String.fromCharCode(65 + (quiz.correct_answer ?? 0))}. {quiz.options[quiz.correct_answer ?? 0]}</span>
              </p>
              {user_attempt?.is_correct && (
                <p className="text-green-400 text-sm mt-2">🎉 獲得 {user_attempt.points_earned} 積分！</p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Action Button */}
      <div className="flex gap-3">
        {!showResult ? (
          <button
            onClick={handleSubmit}
            disabled={selectedAnswer === null || isSubmitting}
            className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold py-3 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? '提交中...' : '提交答案'}
          </button>
        ) : (
          <>
            {quizData.remaining_attempts > 0 ? (
              <button
                onClick={handleNextQuiz}
                className="flex-1 bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold py-3 rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all"
              >
                下一題 ({quizData.remaining_attempts} 題待答)
              </button>
            ) : (
              <div className="flex-1 bg-gray-800/50 text-gray-400 font-semibold py-3 rounded-lg text-center">
                🎉 今日題目全部完成！
              </div>
            )}
          </>
        )}
      </div>

      {/* Movie Reference */}
      {quiz.movie_reference && (
        <div className="mt-4 pt-4 border-t border-gray-700">
          <p className="text-sm text-gray-400">
            💡 電影：<span className="text-purple-400 font-semibold">{quiz.movie_reference.title}</span> ({quiz.movie_reference.year})
          </p>
        </div>
      )}
    </motion.div>
  );
}
