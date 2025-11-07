// [重要！] 導入 Suspense
import { Suspense } from 'react';
// 導入我們新建立的 ResetPasswordForm Wrapper
import { ResetPasswordFormWrapper } from '../../features/auth';

// 建立一個 Loading 元件 (可選, 但推薦)
function LoadingFallback() {
  return <div className="p-10 text-center">載入中...</div>
}

export default function ResetPasswordPage() {
  
  return (
    // 我們使用和 Login 頁面完全相同的「黑色背景」佈局
    <div className="relative min-h-screen bg-black py-20">

      {/* --- 文字 LOGO --- */}
      <div className="absolute top-8 left-8">
        <h1 className="text-3xl font-bold text-white tracking-wider">
          MovieIN
        </h1>
      </div>
      {/* --- LOGO 結束 --- */}


      {/* --- 兩欄式佈局 --- */}
      <div className="w-full max-w-4xl mx-auto">
        <div className="shadow-lg rounded-lg overflow-hidden flex items-stretch">
          
          {/* 1. 左半邊 (圖片) */}
          <div 
            className="w-1/2 hidden lg:block bg-cover bg-center min-h-[600px]" 
            style={{ backgroundImage: "url('/img/reset-password-bg.jpg')" }} 
          >
          </div>

          {/* 2. 右半邊 (我們的表單) */}
          <div className="w-full lg:w-1/2 bg-white">
            {/* [關鍵！] 
              我們必須使用 <Suspense> 包裹 ResetPasswordFormWrapper,
              因為它內部的 useSearchParams() 只能在 Client 渲染
            */}
            <Suspense fallback={<LoadingFallback />}>
              <ResetPasswordFormWrapper />
            </Suspense>
          </div>

        </div>
      </div>
      {/* --- 兩欄式佈局結束 --- */}

    </div>
  );
}