'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import {
  FaSearch,
  FaUserCircle,
  FaHeart,
  FaListAlt,
  FaCog,
  FaSignOutAlt,
  FaBars,
  FaTimes,
  FaUsers,
  FaEnvelope,
} from 'react-icons/fa';

import { Api } from '../lib/api';
import { getJSON } from '@/lib/http';
import { UserPublic } from '../lib/types/user';
import { LogoutModal } from './LogoutModal';

export default function NavBar() {
  const router = useRouter();
  const pathname = usePathname();
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);
  const [user, setUser] = useState<UserPublic | null>(null);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [messagesCount, setMessagesCount] = useState<number>(0);
  const timeoutRef = useRef<number | null>(null);
  const pollRef = useRef<number | null>(null);

  const fetchUser = async () => {
    try {
      const userData = await Api.profile.me();
      setUser(userData);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      localStorage.removeItem('authToken');
      router.push('/login');
    }
  };

  useEffect(() => {
    fetchUser();

    // load pending friend requests count for badge (defensive)
    const loadPending = async () => {
      try {
        // Prefer an endpoint that returns only a count for efficiency
        const res = await getJSON<{ count: number }>('/friends/requests/count');
        const n = res && typeof res.count === 'number' ? res.count : 0;
        setPendingCount(n);
      } catch (e) {
        console.error('Failed to load pending friend requests count:', e);
        // On error, ensure badge is hidden by setting 0
        setPendingCount(0);
      }
    };
    loadPending();

    const loadMessagesCount = async () => {
      try {
        const js = await Api.messages.unreadCount();
        setMessagesCount(js?.count ?? 0);
      } catch (e) {
        setMessagesCount(0);
      }
    };
    loadMessagesCount();

    const handleProfileUpdate = () => fetchUser();
    window.addEventListener('profileUpdated', handleProfileUpdate);

    const handleFriendUpdate = () => {
      loadPending();
      loadMessagesCount();
    };
    window.addEventListener('friendRequestsUpdated', handleFriendUpdate as EventListener);

    const handleConversationsUpdated = (ev: Event) => {
      // If the event includes a detail with `marked` count, optimistically subtract it.
      try {
        const ce = ev as CustomEvent<any>;
        const detail = ce?.detail;
        if (detail && typeof detail.marked === 'number') {
          setMessagesCount((prev) => Math.max(0, prev - detail.marked));
        } else {
          // otherwise reload from server
          loadMessagesCount();
        }
      } catch (e) {
        loadMessagesCount();
      }
    };
    window.addEventListener('conversationsUpdated', handleConversationsUpdated as EventListener);

    // Poll unread count periodically so badge updates when other users send messages.
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
    pollRef.current = window.setInterval(() => {
      loadMessagesCount();
    }, 5000);

    const handleWindowFocus = () => loadMessagesCount();
    const handleVisibility = () => {
      if (document.visibilityState === 'visible') loadMessagesCount();
    };
    window.addEventListener('focus', handleWindowFocus);
    document.addEventListener('visibilitychange', handleVisibility);

    return () => {
      window.removeEventListener('profileUpdated', handleProfileUpdate);
      window.removeEventListener('friendRequestsUpdated', handleFriendUpdate as EventListener);
      window.removeEventListener('conversationsUpdated', handleConversationsUpdated as EventListener);
      window.removeEventListener('focus', handleWindowFocus);
      document.removeEventListener('visibilitychange', handleVisibility);
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [router]);

  const handleMouseEnter = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setIsProfileOpen(true);
  };

  const handleMouseLeave = () => {
    timeoutRef.current = window.setTimeout(() => setIsProfileOpen(false), 150);
  };

  const performLogout = () => {
    localStorage.removeItem('authToken');
    setUser(null);
    console.log('使用者已登出');
    setIsLogoutModalOpen(false);
    router.push('/login');
  };

  const handleOpenLogoutModal = () => {
    setIsProfileOpen(false);
    setIsLogoutModalOpen(true);
  };

  const linkCls = (p: string) =>
    `px-3 py-2 rounded transition-all duration-300 ${
      pathname === p 
        ? 'font-bold text-white bg-purple-600/20 border-b-2 border-purple-400' 
        : 'text-gray-400 hover:text-white hover:bg-white/5'
    }`;

  const handleSearchSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const query = formData.get('search') as string;
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <>
      <nav className="sticky top-0 z-50 w-full bg-gray-900 shadow">
        <div className="relative flex items-center justify-between px-4 md:px-6 py-3">
          {/* === 左側 Logo + Hamburger === */}
          <div className="flex items-center space-x-4 z-10">
            {/* Hamburger Menu Button (Mobile) */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden text-white text-2xl hover:text-purple-400 transition-colors"
              aria-label="選單"
            >
              {isMobileMenuOpen ? <FaTimes /> : <FaBars />}
            </button>

            <Link href="/home" className="text-white text-2xl md:text-3xl font-bold hover:text-purple-400 transition-colors">
              MovieIN
            </Link>
            
            {/* === 主導航連結 (Desktop) === */}
            <nav className="hidden md:flex items-center space-x-1">
              <Link href="/home" className={linkCls('/home')}>
                首頁
              </Link>
              <Link href="/recommendation" className={linkCls('/recommendation')}>
                推薦
              </Link>
              <Link href="/popular" className={linkCls('/popular')}>
                熱門
              </Link>
              <Link href="/social" className={linkCls('/social')}>
                交友
              </Link>
              <Link href="/search" className={linkCls('/search')}>
                搜尋
              </Link>
            </nav>
          </div>

          {/* === 中間搜尋欄 (Desktop & Tablet) - 絕對置中 === */}
          <div className="hidden sm:block absolute left-1/2 -translate-x-1/2 w-full max-w-md px-4">
            <form className="relative w-full" onSubmit={handleSearchSubmit}>
              <input
                type="text"
                name="search"
                className="block w-full bg-white border border-gray-300 rounded-lg py-2 pl-4 pr-10 text-sm text-gray-700 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="搜尋電影、活動、節目..."
              />
              <button
                type="submit"
                className="absolute inset-y-0 right-0 flex items-center pr-3 hover:text-purple-500 transition-colors"
              >
                <FaSearch className="h-5 w-5 text-gray-400" />
              </button>
            </form>
          </div>

          {/* === 右側使用者頭像區 === */}
          <div className="flex items-center space-x-2 md:space-x-3 z-10">
            {/* Mobile Search Icon */}
            <Link href="/search" className="sm:hidden text-white text-xl hover:text-purple-400 transition-colors">
              <FaSearch />
            </Link>

            <Link href="/messages" className="relative text-white text-xl hover:text-purple-400 transition-colors">
              <FaEnvelope />
              {messagesCount > 0 && (
                <span className="absolute -top-1 -right-2 inline-flex items-center justify-center px-2 py-0.5 text-xs font-semibold rounded-full bg-red-600 text-white">{messagesCount}</span>
              )}
            </Link>

            <li
              className="relative list-none"
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
            >
              <button
                className="flex items-center space-x-2"
                onClick={() => setIsProfileOpen(!isProfileOpen)}
              >
                {/* 使用者名稱 */}
                <span
                  className="hidden lg:inline text-gray-400 text-lg truncate max-w-[140px] inline-block align-middle"
                  title={user?.profile?.display_name || ''}
                >
                  {user ? user.profile?.display_name : '載入中...'}
                </span>

                {/* 頭像 */}
                <img
                  className="h-8 w-8 md:h-10 md:w-10 rounded-full object-cover ring-2 ring-gray-700 hover:ring-purple-500 transition-all"
                  src={user?.profile?.avatar_url || '/img/default-avatar.jpg'}
                  alt={user?.profile?.display_name || '使用者'}
                />
              </button>

              {/* 下拉選單 */}
              {isProfileOpen && (
                <div className="absolute right-0 z-50 mt-2 w-48 bg-white rounded-md shadow-lg py-1">
                  <Link
                    href="/profile?tab=profile"
                    onClick={() => setIsProfileOpen(false)}
                    className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <FaUserCircle className="mr-2 h-5 w-5 text-gray-400" />
                    個人資料
                  </Link>
                      <Link
                        href="/social/friends"
                        onClick={() => setIsProfileOpen(false)}
                        className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <FaUsers className="mr-2 h-5 w-5 text-gray-400" />
                        <span className="flex items-center gap-2">
                          好友
                          {pendingCount > 0 && (
                            <span className="ml-1 inline-flex items-center justify-center px-2 py-0.5 text-xs font-semibold rounded-full bg-red-600 text-white">
                              {pendingCount}
                            </span>
                          )}
                        </span>
                      </Link>
                  <Link
                    href="/profile?tab=watchlist"
                    onClick={() => setIsProfileOpen(false)}
                    className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <FaListAlt className="mr-2 h-5 w-5 text-gray-400" />
                    待看清單
                  </Link>
                  <Link
                    href="/profile?tab=lists"
                    onClick={() => setIsProfileOpen(false)}
                    className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <FaHeart className="mr-2 h-5 w-5 text-gray-400" />
                    我的片單
                  </Link>
                  <Link
                    href="/profile?tab=settings"
                    onClick={() => setIsProfileOpen(false)}
                    className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <FaCog className="mr-2 h-5 w-5 text-gray-400" />
                    帳戶設定
                  </Link>

                  <div className="border-t border-gray-100 my-1"></div>

                  <button
                    onClick={handleOpenLogoutModal}
                    className="w-full text-left flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <FaSignOutAlt className="mr-2 h-5 w-5 text-gray-400" />
                    登出
                  </button>
                </div>
              )}
            </li>
          </div>
        </div>

        {/* === Mobile Menu Drawer === */}
        {isMobileMenuOpen && (
          <div className="md:hidden bg-gray-800 border-t border-gray-700">
            {/* Mobile Search Bar */}
            <div className="px-4 py-3 sm:hidden">
              <form className="relative w-full" onSubmit={(e) => {
                handleSearchSubmit(e);
                setIsMobileMenuOpen(false);
              }}>
                <input
                  type="text"
                  name="search"
                  className="block w-full bg-white border border-gray-300 rounded-lg py-2 pl-4 pr-10 text-sm text-gray-700 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="搜尋電影..."
                />
                <button
                  type="submit"
                  className="absolute inset-y-0 right-0 flex items-center pr-3 hover:text-purple-500 transition-colors"
                >
                  <FaSearch className="h-5 w-5 text-gray-400" />
                </button>
              </form>
            </div>

            {/* Mobile Navigation Links */}
            <nav className="flex flex-col py-2">
              <Link 
                href="/home" 
                onClick={() => setIsMobileMenuOpen(false)}
                className={`px-4 py-3 text-base transition-colors ${
                  pathname === '/home' 
                    ? 'bg-purple-600/20 text-white font-bold border-l-4 border-purple-400' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                首頁
              </Link>
              <Link 
                href="/recommendation" 
                onClick={() => setIsMobileMenuOpen(false)}
                className={`px-4 py-3 text-base transition-colors ${
                  pathname === '/recommendation' 
                    ? 'bg-purple-600/20 text-white font-bold border-l-4 border-purple-400' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                推薦
              </Link>
              <Link 
                href="/popular" 
                onClick={() => setIsMobileMenuOpen(false)}
                className={`px-4 py-3 text-base transition-colors ${
                  pathname === '/popular' 
                    ? 'bg-purple-600/20 text-white font-bold border-l-4 border-purple-400' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                熱門
              </Link>
              <Link 
                href="/social" 
                onClick={() => setIsMobileMenuOpen(false)}
                className={`px-4 py-3 text-base transition-colors ${
                  pathname === '/social' 
                    ? 'bg-purple-600/20 text-white font-bold border-l-4 border-purple-400' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                交友
              </Link>
              <Link 
                href="/social/friends" 
                onClick={() => setIsMobileMenuOpen(false)}
                className={`px-4 py-3 text-base transition-colors ${
                  pathname === '/social/friends' 
                    ? 'bg-purple-600/20 text-white font-bold border-l-4 border-purple-400' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span>好友</span>
                  {pendingCount > 0 && (
                    <span className="inline-flex items-center justify-center px-2 py-0.5 text-xs font-semibold rounded-full bg-red-600 text-white">
                      {pendingCount}
                    </span>
                  )}
                </div>
              </Link>
              <Link 
                href="/search" 
                onClick={() => setIsMobileMenuOpen(false)}
                className={`px-4 py-3 text-base transition-colors ${
                  pathname === '/search' 
                    ? 'bg-purple-600/20 text-white font-bold border-l-4 border-purple-400' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                搜尋
              </Link>
            </nav>
          </div>
        )}
      </nav>

      {/* 登出確認 Modal */}
      <LogoutModal
        isOpen={isLogoutModalOpen}
        onClose={() => setIsLogoutModalOpen(false)}
        onConfirm={performLogout}
      />
    </>
  );
}
