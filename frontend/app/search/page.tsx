'use client';

import { motion } from 'framer-motion';
import { PageLayout } from '@/components/layouts';
import SearchForm from '@/features/search/SearchForm';

export default function SearchPage() {
  return (
    <PageLayout>
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1.5, ease: "easeOut" }}
        className="space-y-8 py-8"
      >
        {/* Page Title with Glow Effect */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-center"
        >
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-3
                       bg-gradient-to-r from-purple-400 via-white to-purple-400 
                       bg-clip-text text-transparent
                       drop-shadow-[0_0_30px_rgba(168,85,247,0.5)]">
            🔍 搜尋電影
          </h1>
          <p className="text-gray-400 text-sm md:text-base">
            在浩瀚的電影宇宙中找到你的目標
          </p>
        </motion.div>

        {/* Search Form */}
        <SearchForm />
      </motion.div>
    </PageLayout>
  );
}
