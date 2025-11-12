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
  const [isPracticeMode, setIsPracticeMode] = useState(false);
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
        practice_mode: isPracticeMode,
      });

      // Update quiz data with result
      setQuizData({
        ...quizData,
        has_answered: !isPracticeMode, // Don't mark as answered in practice mode
        daily_attempts: isPracticeMode ? quizData.daily_attempts : quizData.daily_attempts + 1,
        remaining_attempts: isPracticeMode ? quizData.remaining_attempts : quizData.remaining_attempts - 1,
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

      // 廣播積分更新事件，讓 Profile 頁面重新載入資料（練習模式不廣播）
      if (result.is_correct && !isPracticeMode) {
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
    setIsPracticeMode(false);
    await fetchTodayQuiz();
  };

  const handlePracticeMode = () => {
    setSelectedAnswer(null);
    setShowResult(false);
    setIsPracticeMode(true);
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
    <div className="space-y-6">
      {/* Section Title - 對齊隨機推薦的設計風格 */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="text-center"
      >
        <h2 className="text-4xl md:text-5xl font-bold mb-3
                     bg-gradient-to-r from-purple-400 via-pink-500 to-red-500
                     bg-clip-text text-transparent
                     drop-shadow-[0_0_30px_rgba(168,85,247,0.6)]">
          每日電影問答
        </h2>
        <p className="text-gray-400 text-sm md:text-base">
          {isPracticeMode ? (
            <span className="text-yellow-400">🔁 練習模式 - 不計分，可重複作答</span>
          ) : (
            <>挑戰你的電影知識，每日 {quizData.daily_limit} 題 • 已完成 {quizData.daily_attempts}/{quizData.daily_limit}</>
          )}
        </p>
      </motion.div>

      {/* Quiz Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-sm border border-gray-700 rounded-2xl p-6 md:p-8 shadow-2xl"
      >
        {/* Header - 簡化版本 */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span className="text-2xl">🎬</span>
            <span>{quiz.category || '電影知識'}</span>
          </div>
          <div className={`px-4 py-2 rounded-full bg-gradient-to-r ${difficultyConfig.color} text-white text-sm font-semibold shadow-lg`}>
            {difficultyConfig.icon} {difficultyConfig.label}
          </div>
        </div>

        {/* Question */}
        <div className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 rounded-xl p-5 mb-6 border border-gray-700/50 shadow-lg">
          <p className="text-white text-lg md:text-xl leading-relaxed font-medium">{quiz.question}</p>
        </div>

        {/* Options or Result */}
        <AnimatePresence mode="wait">
          {!showResult ? (
            <motion.div
              key="options"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-3 mb-6"
            >
              {quiz.options.map((option, index) => (
                <motion.button
                  key={index}
                  onClick={() => setSelectedAnswer(index)}
                  disabled={isSubmitting}
                  whileHover={{ scale: selectedAnswer === index ? 1 : 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={`w-full text-left px-5 py-4 rounded-xl transition-all duration-200 ${
                    selectedAnswer === index
                      ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white border-2 border-purple-400 shadow-lg shadow-purple-500/50'
                      : 'bg-gray-800/50 text-gray-300 border-2 border-gray-700 hover:border-purple-500/50 hover:bg-gray-800/70'
                  }`}
                >
                  <span className="font-bold mr-3 text-lg">{String.fromCharCode(65 + index)}.</span>
                  <span className="text-base">{option}</span>
                </motion.button>
              ))}
            </motion.div>
          ) : (
            <motion.div
              key="result"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
              className="mb-6"
            >
              <div className={`rounded-xl p-6 shadow-xl ${
                user_attempt?.is_correct 
                  ? 'bg-gradient-to-br from-green-900/40 to-emerald-900/40 border-2 border-green-500/60' 
                  : 'bg-gradient-to-br from-red-900/40 to-rose-900/40 border-2 border-red-500/60'
              }`}>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-4xl">{user_attempt?.is_correct ? '✅' : '❌'}</span>
                    <span className={`font-bold text-xl ${
                      user_attempt?.is_correct ? 'text-green-300' : 'text-red-300'
                    }`}>
                      {user_attempt?.is_correct ? '答對了！' : '答錯了'}
                    </span>
                  </div>
                  {user_attempt?.is_correct && !isPracticeMode && (
                    <div className="bg-yellow-500/20 border border-yellow-500/50 px-4 py-2 rounded-lg">
                      <span className="text-yellow-300 font-bold text-lg">+{user_attempt.points_earned} 分</span>
                    </div>
                  )}
                  {isPracticeMode && (
                    <div className="bg-blue-500/20 border border-blue-500/50 px-4 py-2 rounded-lg">
                      <span className="text-blue-300 font-bold text-sm">🔁 練習模式</span>
                    </div>
                  )}
                </div>
                <div className="bg-gray-900/50 rounded-lg p-4 backdrop-blur-sm">
                  <p className="text-gray-300 text-sm mb-1">正確答案：</p>
                  <p className="text-white font-semibold text-base">
                    {String.fromCharCode(65 + (quiz.correct_answer ?? 0))}. {quiz.options[quiz.correct_answer ?? 0]}
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Action Button */}
        <div className="flex gap-3">
          {!showResult ? (
            <motion.button
              onClick={handleSubmit}
              disabled={selectedAnswer === null || isSubmitting}
              whileHover={{ scale: selectedAnswer !== null ? 1.02 : 1 }}
              whileTap={{ scale: 0.98 }}
              className={`flex-1 font-bold py-4 rounded-xl transition-all shadow-lg ${
                selectedAnswer !== null && !isSubmitting
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700 hover:shadow-purple-500/50'
                  : 'bg-gray-700 text-gray-400 cursor-not-allowed'
              }`}
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                  />
                  提交中...
                </span>
              ) : '提交答案'}
            </motion.button>
          ) : (
            <>
              {isPracticeMode ? (
                // Practice Mode - Show retry button
                <motion.button
                  onClick={() => {
                    setSelectedAnswer(null);
                    setShowResult(false);
                  }}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex-1 bg-gradient-to-r from-orange-600 to-yellow-600 text-white font-bold py-4 rounded-xl hover:from-orange-700 hover:to-yellow-700 transition-all shadow-lg hover:shadow-orange-500/50"
                >
                  <span className="flex items-center justify-center gap-2">
                    🔁 再試一次
                  </span>
                </motion.button>
              ) : quizData.remaining_attempts > 0 ? (
                <motion.button
                  onClick={handleNextQuiz}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex-1 bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-bold py-4 rounded-xl hover:from-blue-700 hover:to-cyan-700 transition-all shadow-lg hover:shadow-blue-500/50"
                >
                  <span className="flex items-center justify-center gap-2">
                    🎬 下一題
                    <span className="bg-white/20 px-2 py-1 rounded-md text-sm">
                      還有 {quizData.remaining_attempts} 題
                    </span>
                  </span>
                </motion.button>
              ) : (
                <div className="flex flex-col gap-3 w-full">
                  <motion.div 
                    initial={{ scale: 0.95 }}
                    animate={{ scale: 1 }}
                    className="bg-gradient-to-r from-green-600/30 to-emerald-600/30 border-2 border-green-500/50 text-green-300 font-bold py-4 rounded-xl text-center shadow-lg"
                  >
                    <span className="flex items-center justify-center gap-2">
                      🎉 今日題目全部完成！
                    </span>
                  </motion.div>
                  
                  {/* Practice Mode Button */}
                  <motion.button
                    onClick={handlePracticeMode}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="bg-gradient-to-r from-orange-600 to-yellow-600 text-white font-bold py-4 rounded-xl hover:from-orange-700 hover:to-yellow-700 transition-all shadow-lg hover:shadow-orange-500/50"
                  >
                    <span className="flex items-center justify-center gap-2">
                      🔁 練習模式
                      <span className="bg-white/20 px-2 py-1 rounded-md text-xs">
                        不計分，可重複作答
                      </span>
                    </span>
                  </motion.button>
                </div>
              )}
            </>
          )}
        </div>

        {/* Movie Reference */}
        {quiz.movie_reference && (
          <div className="mt-6 pt-6 border-t border-gray-700/50">
            <p className="text-sm text-gray-400 flex items-center gap-2">
              <span className="text-base">💡</span>
              <span>
                電影：<span className="text-purple-400 font-semibold">{quiz.movie_reference.title}</span>
                <span className="text-gray-500 ml-2">({quiz.movie_reference.year})</span>
              </span>
            </p>
          </div>
        )}
      </motion.div>
    </div>
  );
}
