// 檔案：frontend/app/register/page.tsx

// 1. 我們導入 RegisterForm (這應該已經是正確的)
import { RegisterForm } from '../../features/auth';

export default function RegisterPage() {
  
  return (
    // 2. 我們使用和 Login 頁面「完全相同」的 'relative min-h-screen bg-black py-20'
    //    來達成「黑色背景」和「可滾動」 (你的需求 #2)
    <div className="relative min-h-screen bg-black py-20">

      {/* --- 3. 我們加上和 Login 頁面「完全相同」的 LOGO --- */}
      <div className="absolute top-8 left-8">
        <h1 className="text-3xl font-bold text-white tracking-wider">
          MovieIN
        </h1>
      </div>
      {/* --- LOGO 結束 --- */}


      {/* --- 4. 我們使用和 Login 頁面「完全相同」的兩欄式卡片佈局 --- */}
      <div className="w-full max-w-4xl mx-auto">
        <div className="shadow-lg rounded-lg overflow-hidden flex items-stretch">
          
          {/* [你的需求 #1：左側圖片]
            (請確認) 你有 'register-bg.jpg' 在 'public/img/' 裡
            (如果沒有，你可以暫時用回 url('/img/login-bg.jpg') )
          */}
          <div 
            className="w-1/2 hidden lg:block bg-cover bg-center min-h-[600px]" 
            style={{ backgroundImage: "url('/img/register-bg.jpg')" }}
          >
            {/* 這裡我們也使用 min-h-[600px] 來確保高度 */}
          </div>

          {/* 2. 右半邊 (我們的註冊表單) */}
          <div className="w-full lg:w-1/2 bg-white">
            {/* 這裡我們放入 <RegisterForm /> 而不是 <LoginForm /> */}
            <RegisterForm />
          </div>

        </div>
      </div>
      {/* --- 兩欄式佈局結束 --- */}

    </div>
  );
}