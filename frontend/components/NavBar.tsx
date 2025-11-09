'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';

export default function NavBar() {
  const pathname = usePathname();

  const linkCls = (p: string) =>
    `px-3 py-2 rounded transition-all duration-300 ${
      pathname === p 
        ? 'font-bold text-white bg-purple-600/20 border-b-2 border-purple-400' 
        : 'text-gray-400 hover:text-white hover:bg-white/5'
    }`;

  return (
    <motion.header 
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="w-full sticky top-0 z-50 border-b border-white/10 bg-black/70 backdrop-blur-xl text-white"
    >
      <nav className="mx-auto max-w-6xl flex items-center gap-4 p-3">
        {/* Logo with glow */}
        <Link href="/" className="text-lg font-semibold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent hover:scale-105 transition-transform">
          MovieIN
        </Link>

        {/* 主頁面連結 */}
        <Link href="/" className={linkCls('/')}>Home</Link>
        <Link href="/recommendation" className={linkCls('/recommendation')}>Recommendation</Link>
        <Link href="/profile" className={linkCls('/profile')}>Profile</Link>
        <Link href="/search" className={linkCls('/search')}>Search</Link>
      </nav>
    </motion.header>
  );
}
