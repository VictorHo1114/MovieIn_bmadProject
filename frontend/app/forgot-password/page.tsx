// 1. 導入我們新建立的 ForgotPasswordForm 元件
import { ForgotPasswordForm } from '../../features/auth';

export default function ForgotPasswordPage() {
  
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
            // (我們重用 login-bg.jpg，或者你可以換成 'bg-password-image' 對應的圖片)
            style={{ backgroundImage: "url('/img/forgot-password-bg.jpg')" }} 
          >
          </div>

          {/* 2. 右半邊 (我們的表單) */}
          <div className="w-full lg:w-1/2 bg-white">
            {/* [關鍵！] 插入 ForgotPasswordForm 元件 */}
            <ForgotPasswordForm />
          </div>

        </div>
      </div>
      {/* --- 兩欄式佈局結束 --- */}

    </div>
  );
}