'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function NavBar() {
  const pathname = usePathname();

  const linkCls = (p: string) =>
    `px-3 py-2 rounded ${pathname === p ? 'font-bold underline' : ''}`;

  return (
    <header className="w-full sticky top-0 z-50 border-b bg-black/70 backdrop-blur text-white">
      <nav className="mx-auto max-w-6xl flex items-center gap-4 p-3">
        {/* Logo */}
        <Link href="/" className="text-lg font-semibold">MovieIN</Link>

        {/* 主頁面連結 */}
        <Link href="/" className={linkCls('/')}>Home</Link>
        <Link href="/profile" className={linkCls('/profile')}>Profile</Link>
        <Link href="/search" className={linkCls('/search')}>Search</Link>
      </nav>
    </header>
  );
}
