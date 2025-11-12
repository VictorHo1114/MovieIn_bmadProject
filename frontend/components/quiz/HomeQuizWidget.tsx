'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Api, type AllTodayQuizzesResponse, type DailyQuiz } from '@/lib/api';
import { QuestionCard } from './QuestionCard';

interface CardState {
  isFlipped: boolean;
  result: {
    is_correct: boolean;
    points_earned: number;
    explanation: string | null;
  } | null;
}

export function HomeQuizWidget() {
  const [allQuizData, setAllQuizData] = useState<AllTodayQuizzesResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // State for each of the 3 cards (no need to track selectedAnswer here)
  const [cardStates, setCardStates] = useState<CardState[]>([
    { isFlipped: false, result: null },
    { isFlipped: false, result: null },
    { isFlipped: false, result: null },
  ]);

  useEffect(() => {
    fetchAllTodayQuizzes();
  }, []);

  const fetchAllTodayQuizzes = async () => {
    try {
      setIsLoading(true);
      const data = await Api.quiz.getAllToday();
      setAllQuizData(data);
      
      // Initialize card states based on existing attempts
      const newCardStates = data.quizzes.map((quiz) => {
        const attempt = data.user_attempts.find(a => a.quiz_id === quiz.id);
        if (attempt) {
          return {
            isFlipped: true,
            result: {
              is_correct: attempt.is_correct,
              points_earned: attempt.points_earned,
              explanation: null, // We'll show quiz explanation on flip
            },
          };
        }
        return { isFlipped: false, result: null };
      });
      setCardStates(newCardStates);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch all quizzes:', err);
      setError('載入失敗');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (answer: number, quizId: number, cardIndex: number) => {
    try {
      const result = await Api.quiz.submit({
        quiz_id: quizId,
        answer: answer,
        time_spent: 15,
        // Backend auto-detects first round, no need to send practice_mode
      });

      // Update card state with result and flip the card
      const newCardStates = [...cardStates];
      newCardStates[cardIndex] = {
        isFlipped: true,
        result: {
          is_correct: result.is_correct,
          points_earned: result.points_earned,
          explanation: null,
        },
      };
      setCardStates(newCardStates);

      // Broadcast points update event if first round and correct
      if (result.is_correct && result.points_earned > 0) {
        window.dispatchEvent(new CustomEvent('quizPointsUpdated'));
      }

      // Update allQuizData to reflect new attempt
      if (allQuizData) {
        setAllQuizData({
          ...allQuizData,
          user_attempts: [
            ...allQuizData.user_attempts,
            {
              id: Date.now(), // Temporary ID
              quiz_id: quizId,
              user_answer: answer,
              is_correct: result.is_correct,
              points_earned: result.points_earned,
              time_spent: 15,
              answered_at: new Date().toISOString(),
            },
          ],
          is_first_round: false, // After first submit, it's no longer first round
        });
      }
    } catch (err: any) {
      console.error('Failed to submit answer:', err);
      alert('提交失敗，請稍後再試');
    }
  };

  const handleReplayAll = () => {
    // Flip all cards back to front (question side)
    setCardStates(prev =>
      prev.map(state => ({
        isFlipped: false,
        result: null,
      }))
    );
  };

  const allCardsAnswered = cardStates.every(state => state.isFlipped);

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

  if (error || !allQuizData || allQuizData.quizzes.length === 0) {
    return null; // No quizzes available
  }

  return (
    <div className="space-y-6">
      {/* Section Title */}
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
          挑戰你的電影知識，每日 {allQuizData.daily_limit} 題 • 已完成 {allQuizData.daily_attempts}/{allQuizData.daily_limit}
          {!allQuizData.is_first_round && (
            <span className="ml-2 text-yellow-400">• 🔁 重玩模式（不計分）</span>
          )}
        </p>
      </motion.div>

      {/* 3 Question Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {allQuizData.quizzes.map((quiz, index) => (
          <QuestionCard
            key={quiz.id}
            quiz={quiz}
            index={index}
            onSubmit={(answer: number) => handleSubmit(answer, quiz.id, index)}
            result={cardStates[index].result}
            isFlipped={cardStates[index].isFlipped}
            isFirstRound={allQuizData.is_first_round}
            disabled={cardStates[index].isFlipped}
          />
        ))}
      </div>

      {/* Replay All Button - Show when all cards are answered */}
      {allCardsAnswered && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex justify-center"
        >
          <motion.button
            onClick={handleReplayAll}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="bg-gradient-to-r from-orange-600 to-yellow-600 text-white font-bold px-8 py-4 rounded-xl hover:from-orange-700 hover:to-yellow-700 transition-all shadow-lg hover:shadow-orange-500/50"
          >
            <span className="flex items-center gap-3">
              <span className="text-2xl">🔄</span>
              <span>再玩一次</span>
              <span className="bg-white/20 px-3 py-1 rounded-md text-sm">
                翻回所有卡片
              </span>
            </span>
          </motion.button>
        </motion.div>
      )}
    </div>
  );
}
