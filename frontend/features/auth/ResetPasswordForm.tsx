'use client'; 

// [重要！] 導入 useSearchParams 來讀取 URL
import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link'; 
import { Api } from '../../lib/api';
import { FaEye, FaEyeSlash } from 'react-icons/fa';

// 我們將在一個 Suspense 邊界中渲染表單
// 這是 Next.js App Router 中使用 useSearchParams 的推薦方式
export function ResetPasswordFormWrapper() {
  return (
    <Suspense fallback={<div className="p-10">讀取中...</div>}>
      <ResetPasswordForm />
    </Suspense>
  );
}

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // --- 1. 狀態管理 ---
  const [token, setToken] = useState<string | null>(null);
  
  // 密碼欄位狀態
  const [newPassword, setNewPassword] = useState('');
  const [repeatPassword, setRepeatPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showRepeatPassword, setShowRepeatPassword] = useState(false);

  // 訊
  const [isLoading, setIsLoading] = useState(false); 
  const [error, setError] = useState<string | null>(null); 
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // --- 2. [關鍵！] 從 URL 讀取 Token ---
  useEffect(() => {
    const tokenFromUrl = searchParams.get('token');
    if (tokenFromUrl) {
      setToken(tokenFromUrl);
    } else {
      // 如果 URL 上沒有 token
      setError("無效的重設連結。請重新申請一次。");
    }
  }, [searchParams]); // 依賴 searchParams

  // --- 3. 提交表單 ---
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    
    // 檢查 Token
    if (!token) {
      setError("無效的重設連結。請重新申請一次。");
      return;
    }
    
    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);

    // 密碼驗證
    if (newPassword !== repeatPassword) {
      setError('新密碼與確認密碼不匹配。');
      setIsLoading(false);
      return; 
    }
    if (newPassword.length < 8) {
      setError('新密碼長度必須至少 8 個字元。');
      setIsLoading(false);
      return;
    }

    try {
      // --- 4. 呼叫 API ---
      await Api.auth.resetPassword({
        token: token,
        new_password: newPassword,
      });

      // --- 成功！---
      setSuccessMessage('密碼已成功重設！您現在可以使用新密碼登入。');
      setIsLoading(false);
      // (可選) 幾秒後自動跳轉
      setTimeout(() => {
        router.push('/login');
      }, 3000); // 3 秒後跳轉

    } catch (err: any) {
      console.error(err);
      // [優化] 處理後端回傳的錯誤
      if (err.message && err.message.includes("400")) {
        setError('重設連結無效或已過期。請重新申請一次。');
      } else {
        setError('發生未預期的錯誤，請稍後再試。'); 
      }
      setIsLoading(false);
    }
  };

  // --- 5. 渲染 (JSX) ---
  return (
    <div className="px-5 py-10 h-full flex flex-col justify-center">

      {/* 狀態 (A)：成功 */}
      {successMessage ? (
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">✅ 密碼已重設</h1>
          <p className="mb-4 text-gray-700">{successMessage}</p>
          <Link className="text-sm text-blue-600 hover:text-blue-800" href="/login">
            立即前往登入
          </Link>
        </div>
      
      /* 狀態 (B)：表單 (或 Token 錯誤) */
      ) : (
        <>
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">設定您的新密碼</h1>
            <p className="mb-4 text-sm text-gray-600">請輸入您的新密碼。 (請確保您是從 Email 連結點擊過來的)</p>
          </div>

          <form className="space-y-4 mt-8" onSubmit={handleSubmit}>
            
            {/* 新密碼 */}
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                className="block w-full rounded-full px-4 py-3 text-sm text-gray-900 border border-gray-300 placeholder-gray-500 shadow-sm pr-10"
                placeholder="新密碼 (至少 8 字元)"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700"
              >
                {showPassword ? <FaEyeSlash className="h-5 w-5" /> : <FaEye className="h-5 w-5" />}
              </button>
            </div>

            {/* 重複新密碼 */}
            <div className="relative">
              <input
                type={showRepeatPassword ? 'text' : 'password'}
                className="block w-full rounded-full px-4 py-3 text-sm text-gray-900 border border-gray-300 placeholder-gray-500 shadow-sm pr-10"
                placeholder="重複輸入新密碼"
                value={repeatPassword}
                onChange={(e) => setRepeatPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowRepeatPassword(!showRepeatPassword)}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700"
              >
                {showRepeatPassword ? <FaEyeSlash className="h-5 w-5" /> : <FaEye className="h-5 w-5" />}
              </button>
            </div>

            {/* 提交按鈕 */}
            <button
              type="submit"
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-full shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400"
              // 如果沒有 token 或正在載入，則禁用
              disabled={isLoading || !token} 
            >
              {isLoading ? '儲存中...' : '儲存新密碼'}
            </button>

            {/* 錯誤訊息 */}
            {error && (
              <p className="text-center text-sm text-red-600">{error}</p>
            )}
          </form>

          <hr className="my-4 border-t border-gray-200" />

          {/* 底部連結 */}
          <div className="text-center mt-2">
            <Link className="text-sm text-blue-600 hover:text-blue-800" href="/login">
              返回登入
            </Link>
          </div>
        </>
      )}
    </div>
  );
}