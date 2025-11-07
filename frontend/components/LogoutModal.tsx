'use client';

import React from 'react';
import { FaSignOutAlt } from 'react-icons/fa';

// 定義 Modal 的 Props (屬性)
interface LogoutModalProps {
  isOpen: boolean;           // 控制 Modal 是否顯示
  onClose: () => void;      // 關閉 Modal 的函式
  onConfirm: () => void;    // 確認登出 (Logout) 的函式
}

export function LogoutModal({ isOpen, onClose, onConfirm }: LogoutModalProps) {
  if (!isOpen) return null;

  return (
    // 遮罩
    <div className="fixed inset-0 z-50 overflow-y-auto bg-gray-900 bg-opacity-50 flex items-center justify-center">
      
      {/* Modal 內容卡片 */}
      <div className="bg-white rounded-lg shadow-xl w-full max-w-sm m-4 transform transition-all">
        
        {/* 標題 */}
        <div className="flex justify-between items-center p-4 border-b">
          <h5 className="text-lg font-bold text-gray-800">確定要登出嗎？</h5>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl" aria-label="Close">
            &times;
          </button>
        </div>
        
        {/* 內文 */}
        <div className="p-4 text-gray-500">
          若您確定要結束目前的登入狀態，請點選下方的「登出」按鈕。
          <br />
          <span className="text-sm text-gray-400">（希望有找到你喜歡的電影！）</span>
        </div>
        
        {/* 底部按鈕 */}
        <div className="flex justify-end space-x-2 p-4 border-t">
          
          {/* 取消按鈕 */}
          <button
            onClick={onClose}
            className="bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-md text-sm"
          >
            取消
          </button>
          
          {/* 登出按鈕 */}
          <button
            onClick={onConfirm}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md text-sm"
          >
            <FaSignOutAlt className="inline mr-1" /> 登出
          </button>
        </div>
      </div>
    </div>
  );
}
