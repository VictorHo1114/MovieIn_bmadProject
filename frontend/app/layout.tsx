// 檔案：frontend/app/layout.tsx (這是修改過的舊檔案)

import './globals.css'; // 假設你的全域 CSS 在這裡

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {/* NavBar 已經從這裡被移除了！*/}
        {/* 這樣 /login 頁面就不會顯示它了 */}
        {children}
      </body>
    </html>
  );
}