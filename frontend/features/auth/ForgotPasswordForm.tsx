'use client'; 

import { useState } from 'react';
import Link from 'next/link'; 
import { Api } from '../../lib/api'; // [注意] 確保路徑是 '../../lib/api'

export function ForgotPasswordForm() {
  
  // [修改！] 我們只需要這四個狀態
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false); 
  const [error, setError] = useState<string | null>(null); 
  // [關鍵！] 新增 successMessage 狀態
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccessMessage(null); // 清除舊訊息

    try {
      // --- 呼叫我們在後端測試過的 API ---
      await Api.auth.forgotPassword({ // [注意] 確保 'Api.auth' 中有 'forgotPassword' 函式
        email: email,
      });

      // --- [關鍵！] 成功！---
      // 我們不跳轉，而是顯示成功訊息
      setSuccessMessage('重設連結已成功發送至您的信箱，請前往點擊連結。');
      setIsLoading(false);

    } catch (err: any) {
      console.error(err);
      // (雖然 API 總是回傳 200，但如果 API 呼叫本身失敗了)
      setError('發生未預期的錯誤，請稍後再試。'); 
      setIsLoading(false);
    }
  };

  // --- 4. HTML -> JSX + Tailwind 翻譯 ---
  return (
    // [修改！] 
    // 1. 'h-full': 讓這個 div 填滿父層的 600px 高度
    // 2. 'flex flex-col': 啟用 Flexbox 垂直佈局
    // 3. 'justify-center': 讓所有內容「垂直置中」
    <div className="px-5 py-10 h-full flex flex-col justify-center">

      {/* [關鍵！] 根據是否有 successMessage 來顯示不同內容 */}
      {successMessage ? (
        
        /* --- 狀態 (B)：成功 --- */
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">✅ 請檢查您的信箱</h1>
          <p className="mb-4 text-gray-700">{successMessage}</p>
          <Link className="text-sm text-blue-600 hover:text-blue-800" href="/login">
            返回登入頁面
          </Link>
        </div>

      ) : (

        /* --- 狀態 (A)：預設表單 --- */
        <>
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">忘記密碼？</h1>
            <p className="mb-4 text-sm text-gray-600">別擔心，輸入您的電子郵件地址，我們會寄送一個重設連結給您。</p>
          </div>

          <form className="space-y-4 mt-8" onSubmit={handleSubmit}>
            
            {/* Email 輸入框 */}
            <div>
              <input
                type="email"
                name="email" 
                className="block w-full rounded-full px-4 py-3 text-sm text-gray-900 border border-gray-300 placeholder-gray-500 shadow-sm"
                placeholder="請輸入您的電子郵件地址..." 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            {/* 登入按鈕 (翻譯 'btn-primary') */}
            <button
              type="submit"
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-full shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400"
              disabled={isLoading} 
            >
              {isLoading ? '發送中...' : '發送重設連結'}
            </button>

            {/* 錯誤訊息 */}
            {error && (
              <p className="text-center text-sm text-red-600">{error}</p>
            )}

          </form>

          <hr className="my-4 border-t border-gray-200" />

          {/* 底部連結 */}
          <div className="text-center">
            <Link className="text-sm text-blue-600 hover:text-blue-800" href="/register">
              建立新帳號！
            </Link>
          </div>
          <div className="text-center mt-2">
            <Link className="text-sm text-blue-600 hover:text-blue-800" href="/login">
              已經有帳號了？登入！
            </Link>
          </div>
        </>
      )}
    </div>
  );
}