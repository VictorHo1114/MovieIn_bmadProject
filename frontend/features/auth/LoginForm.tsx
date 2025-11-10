  'use client'; 

  import { useState } from 'react';
  import { useRouter } from 'next/navigation';
  import Link from 'next/link'; 
  import { Api } from '../../lib/api'; 
  import { FaGoogle, FaFacebookF, FaEye, FaEyeSlash } from 'react-icons/fa'; 
  // [修正！] 新增 FaEye 和 FaEyeSlash

  export function LoginForm() {
    const router = useRouter(); 

    const [showPassword, setShowPassword] = useState(false);

    const [error, setError] = useState<string | null>(null); 
    const [isLoading, setIsLoading] = useState(false); 

    // --- 表單處理方式 (邏輯保持不變) ---
    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      setIsLoading(true);
      setError(null);

      const formData = new FormData(event.currentTarget);
      const email = formData.get('email') as string;
      const password = formData.get('password') as string;
      
      if (!email || !password) {
        setError('請輸入電子郵件與密碼。'); 
        setIsLoading(false);
        return;
      }

      try {
        const authToken = await Api.auth.login({
          email: email,
          password: password,
        });

        localStorage.setItem('authToken', authToken.access_token);
        console.log('登入成功:', authToken);
        
        router.push('/home');

      } catch (err: any) {
        console.error(err);
        setError('電子郵件或密碼錯誤，請重試。'); 
      } finally {
        setIsLoading(false);
      }
    };

    // --- 4. HTML -> JSX + Tailwind 翻譯 (修正註解) ---
    return (
      <div className="px-5 py-10">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Movie Time！</h1> 
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          
          {/* Email 輸入框 */}
          <div>
            {/* [修正 1] 將中文註解移到標籤外面 */}
            <input
              type="email"
              name="email" 
              className="block w-full rounded-full px-4 py-3 text-sm text-gray-900 border border-gray-300 placeholder-gray-500 shadow-sm"
              placeholder="請輸入電子郵件地址..." 
              required
            />
          </div>

          {/* 密碼輸入框 */}
          <div>
            <div className="relative"> {/* 新增 relative 容器 */}
              <input
                type={showPassword ? 'text' : 'password'} // 動態切換 type
                name="password"
                className="block w-full rounded-full px-4 py-3 text-sm text-gray-900 border border-gray-300 placeholder-gray-500 shadow-sm pr-10" // 新增 pr-10 給按鈕留空間
                placeholder="密碼"
                required
              />
              {/* [修正！] 密碼切換按鈕，使用 FaEye 圖示 */}
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                // 將按鈕絕對定位在輸入框右側，與 PasswordInput 元件的樣式相同
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700"
              >
                {showPassword ? (
                  <FaEyeSlash className="h-5 w-5" /> // 眼睛斜線圖示
                ) : (
                  <FaEye className="h-5 w-5" /> // 眼睛圖示
                )}
              </button>
            </div>
          </div>

          {/* 記住我 (保持不變) */}
          <div className="flex items-center">
            <input
              id="customCheck"
              type="checkbox"
              className="h-4 w-4 text-blue-600 border-gray-300 rounded"
            />
            <label htmlFor="customCheck" className="ml-2 block text-sm text-gray-900">
              記住我 
            </label>
          </div>

          {/* 登入按鈕 (保持不變) */}
          <button
            type="submit"
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-full shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400"
            disabled={isLoading} 
          >
            {isLoading ? '登入中...' : '登入'} 
          </button>

          {/* 錯誤訊息 (保持不變) */}
          {error && (
            <p className="text-center text-sm text-red-600">{error}</p>
          )}

        </form>

        <hr className="my-4 border-t border-gray-200" />

        {/* 其他登入方式 (保持不變) */}
        <div className="space-y-3">
          <button
            type="button"
            className="w-full flex justify-center items-center py-3 px-4 border border-gray-300 rounded-full shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <FaGoogle className="mr-2 text-red-500" /> 使用 Google 登入 
          </button>
          <button
            type="button"
            className="w-full flex justify-center items-center py-3 px-4 border border-gray-300 rounded-full shadow-sm text-sm font-medium text-white bg-blue-800 hover:bg-blue-900"
          >
            <FaFacebookF className="mr-2" /> 使用 Facebook 登入 
          </button>
        </div>
        
        <hr className="my-4 border-t border-gray-200" />

        {/* 底部連結 (保持不變) */}
        <div className="text-center">
          <Link className="text-sm text-blue-600 hover:text-blue-800" href="/forgot-password">
            忘記密碼？ 
          </Link>
        </div>
        <div className="text-center mt-2">
          <Link className="text-sm text-blue-600 hover:text-blue-800" href="/register">
            建立新帳號！ 
          </Link>
        </div>
      </div>
    );
  }