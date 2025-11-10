'use client';

import './globals.css';
import { usePathname } from 'next/navigation';
import NavBar from '../components/NavBar';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  
  // 不需要 NavBar 的頁面路徑
  const noNavBarPages = ['/login', '/register', '/forgot-password', '/reset-password', '/'];

  const shouldShowNavBar = !noNavBarPages.includes(pathname);

  return (
    <html lang="zh-TW">
      <body>
        {shouldShowNavBar && <NavBar />}
        <main>
          {children}
        </main>
      </body>
    </html>
  );
}
