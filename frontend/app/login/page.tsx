// 檔案：frontend/app/login/page.tsx (完整替換)

import { LoginForm } from '../../features/auth';

export default function LoginPage() {
  
  return (
    <div className="relative min-h-screen bg-black py-20">

      {/* --- 文字 LOGO (保持不變) --- */}
      <div className="absolute top-8 left-8">
        <h1 className="text-3xl font-bold text-white tracking-wider">
          MovieIN
        </h1>
      </div>
      {/* --- LOGO 結束 --- */}


      {/* --- 兩欄式佈局 (保持不變) --- */}
      <div className="w-full max-w-4xl mx-auto">
        {/*
          [重要修改] 我們在這裡加上 'items-stretch' 
          這會確保右邊的表單 (如果比較短) 會被拉伸
          以填滿左邊圖片的高度
        */}
        <div className="shadow-lg rounded-lg overflow-hidden flex items-stretch">
          
          {/* 1. 左半邊 (圖片) */}
          <div 
            // [關鍵修改!] 
            // 1. 我們換回 'bg-cover' (看起來更專業)
            // 2. 我們用 'min-h-[600px]' (Tailwind 語法) 
            //    來強行定義最小高度
            className="w-1/2 hidden lg:block bg-cover bg-center min-h-[600px]" 
            style={{ backgroundImage: "url('/img/login-bg.jpg')" }}
          >
            {/* (你也可以用 style={{ minHeight: '600px' }})
              (你可以隨意調整 600px 這個數字，
               例如 500px 或 700px，直到你滿意為止)
            */}
          </div>

          {/* 2. 右半邊 (我們的表單) */}
          {/* (保持不變) 
            這個 <div> 現在會自動被 'items-stretch' 拉伸
            到 600px 高
          */}
          <div className="w-full lg:w-1/2 bg-white">
            <LoginForm />
          </div>

        </div>
      </div>
      {/* --- 兩欄式佈局結束 --- */}

    </div>
  );
}