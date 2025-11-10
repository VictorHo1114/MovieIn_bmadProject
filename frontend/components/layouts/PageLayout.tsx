"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface PageLayoutProps {
  children: ReactNode;
  className?: string;
  showFooter?: boolean;
}

/**
 * 統一的頁面佈局組件
 * - 深空漸層背景 (from-gray-900 via-black to-black)
 * - 左右留邊 (max-w-7xl mx-auto px-4 md:px-6 lg:px-8)
 * - Footer 支援
 */
export function PageLayout({ 
  children, 
  className = "", 
  showFooter = true 
}: PageLayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-black to-black text-white flex flex-col">
      {/* Main Content Area */}
      <main className={`flex-1 ${className}`}>
        <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8">
          {children}
        </div>
      </main>

      {/* Footer */}
      {showFooter && (
        <motion.footer 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="border-t border-white/10 py-6 mt-auto"
        >
          <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8">
            <div className="text-center">
              <p className="text-gray-500 text-sm">
                 2025 MovieIn. All rights reserved.
              </p>
            </div>
          </div>
        </motion.footer>
      )}
    </div>
  );
}
