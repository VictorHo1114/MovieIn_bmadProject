'use client'; 

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link'; // 用 Next.js 的 Link 來導航
import { Api } from '@/lib/api'; // [注意] 保持使用 '@/lib/api' 捷徑，這是正確的導入方式
import { FaGoogle, FaFacebookF, FaEye, FaEyeSlash } from 'react-icons/fa';

export function RegisterForm() {
  const router = useRouter();

  // --- 1. React 狀態 (State) ---
  const [showPassword, setShowPassword] = useState(false);
  const [showRepeatPassword, setShowRepeatPassword] = useState(false);
  
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [repeatPassword, setRepeatPassword] = useState(''); 

  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // --- 2. React 表單處理 (Submit Handler) ---
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); 
    setIsLoading(true);
    setError(null);

    // --- 3. 客戶端驗證 (在地化為中文) ---
    if (password !== repeatPassword) {
      setError('新密碼與確認密碼不匹配，請檢查。'); // [在地化文本]
      setIsLoading(false);
      return; 
    }
    
    if (password.length < 8) {
      setError('密碼長度必須至少 8 個字元。'); // [在地化文本]
      setIsLoading(false);
      return;
    }

    try {
      // --- 4. 呼叫 API ---
      console.log('註冊資料:', { email, password: '***', display_name: displayName }); // Debug log
      
      await Api.auth.signup({
        email: email,
        password: password,
        display_name: displayName,
      });

      // 註冊成功！
      alert('註冊成功！即將導向登入頁面。');
      router.push('/login'); // 導向登入頁面

    } catch (err: any) {
      console.error('註冊錯誤詳情:', err);
      
      // [優化] 錯誤處理 (在地化為中文)
      if (err.message && err.message.includes("Email already registered")) {
        setError('該電子郵件已被註冊，請直接登入。'); // [在地化文本]
      } else if (err.message) {
        setError(`錯誤: ${err.message}`); // 顯示詳細錯誤訊息
      } else {
        setError('發生未預期錯誤，請稍後再試。'); // [在地化文本]
      }
    } finally {
      setIsLoading(false);
    }
  };

  // --- 5. HTML -> JSX + Tailwind 翻譯 (所有文本替換為中文) ---
  return (
    <div className="px-5 py-10">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">建立新帳號！</h1> {/* [修改文本] */}
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        
        {/* 顯示名稱 (Display Name) */}
        <div>
          <input
            type="text"
            className="block w-full rounded-full px-4 py-3 text-sm text-gray-900 border border-gray-300 placeholder-gray-500 shadow-sm"
            placeholder="顯示名稱" // [修改文本]
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
          />
        </div>
        
        {/* Email */}
        <div>
          <input
            type="email"
            className="block w-full rounded-full px-4 py-3 text-sm text-gray-900 border border-gray-300 placeholder-gray-500 shadow-sm"
            placeholder="電子郵件地址" // [修改文本]
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        {/* 密碼和重複密碼 */}
        <div className="flex flex-col sm:flex-row sm:space-x-4 space-y-4 sm:space-y-0">
      
      {/* 密碼欄 */}
      <div className="sm:w-1/2 relative">
        <input
          type={showPassword ? "text" : "password"}
          className="block w-full rounded-full px-4 py-3 text-sm text-gray-900 border border-gray-300 placeholder-gray-500 shadow-sm pr-10"
          placeholder="密碼 (至少 8 字元)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {/* 顯示/隱藏按鈕 */}
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
        >
          {showPassword ? (
            <FaEyeSlash className="h-5 w-5" />
          ) : (
            <FaEye className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* 重複密碼欄 */}
      <div className="sm:w-1/2 relative">
        <input
          type={showRepeatPassword ? "text" : "password"}
          className="block w-full rounded-full px-4 py-3 text-sm text-gray-900 border border-gray-300 placeholder-gray-500 shadow-sm pr-10"
          placeholder="重複輸入密碼"
          value={repeatPassword}
          onChange={(e) => setRepeatPassword(e.target.value)}
          required
        />
        {/* 顯示/隱藏按鈕 */}
        <button
          type="button"
          onClick={() => setShowRepeatPassword(!showRepeatPassword)}
          className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
        >
          {showRepeatPassword ? (
            <FaEyeSlash className="h-5 w-5" />
          ) : (
            <FaEye className="h-5 w-5" />
          )}
        </button>
      </div>
    </div>

        {/* 註冊按鈕 */}
        <button
          type="submit"
          className="w-full flex justify-center py-3 px-4 border border-transparent rounded-full shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400"
          disabled={isLoading}
        >
          {isLoading ? '建立帳號中...' : '註冊帳號'} {/* [修改文本] */}
        </button>
        
        {/* 顯示 API 回傳的錯誤 */}
        {error && (
          <p className="text-center text-sm text-red-600">{error}</p>
        )}

      </form>

      <hr className="my-4 border-t border-gray-200" />

      {/* 其他登入方式 */}
      <div className="space-y-3">
        <button
          type="button"
          className="w-full flex justify-center items-center py-3 px-4 border border-gray-300 rounded-full shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <FaGoogle className="mr-2 text-red-500" /> 使用 Google 註冊 {/* [修改文本] */}
        </button>
        <button
          type="button"
          className="w-full flex justify-center items-center py-3 px-4 border border-gray-300 rounded-full shadow-sm text-sm font-medium text-white bg-blue-800 hover:bg-blue-900"
        >
          <FaFacebookF className="mr-2" /> 使用 Facebook 註冊 {/* [修改文本] */}
        </button>
      </div>
      
      <hr className="my-4 border-t border-gray-200" />

      {/* 底部連結 */}
      <div className="text-center">
        <Link className="text-sm text-blue-600 hover:text-blue-800" href="/forgot-password">
          忘記密碼？ {/* [修改文本] */}
        </Link>
      </div>
      <div className="text-center mt-2">
        <Link className="text-sm text-blue-600 hover:text-blue-800" href="/login">
          已經有帳號了？登入！ {/* [修改文本] */}
        </Link>
      </div>
    </div>
  );
}