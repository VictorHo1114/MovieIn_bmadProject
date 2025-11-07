'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  FaSearch,
  FaUserCircle,
  FaHeart,
  FaListAlt,
  FaCog,
  FaSignOutAlt,
} from 'react-icons/fa';

import { Api } from '../lib/api';
import { UserPublic } from '../lib/types/user';
import { LogoutModal } from './LogoutModal';

export function NavBar() {
  const router = useRouter();
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);
  const [user, setUser] = useState<UserPublic | null>(null);
  const timeoutRef = useRef<number | null>(null);

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

    const handleProfileUpdate = () => fetchUser();
    window.addEventListener('profileUpdated', handleProfileUpdate);
    return () => window.removeEventListener('profileUpdated', handleProfileUpdate);
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

  return (
    <>
      <nav className="sticky top-0 z-50 flex items-center justify-between w-full px-6 py-3 bg-gray-900 shadow mb-4 flex-wrap">
        {/* === 左側 Logo === */}
        <div className="flex-1 flex justify-start min-w-[120px]">
          <Link href="/home" className="text-white text-3xl font-bold">
            MovieIN
          </Link>
        </div>

        {/* === 中間搜尋欄 === */}
        <div className="flex-1 flex justify-center w-full max-w-md mx-auto">
          <form className="relative w-full">
            <input
              type="text"
              className="block w-full bg-white border border-gray-300 rounded-lg py-2 pl-4 pr-10 text-sm text-gray-500 placeholder-gray-500"
              placeholder="搜尋電影、活動、節目..."
            />
            <button
              type="submit"
              className="absolute inset-y-0 right-0 flex items-center pr-3"
            >
              <FaSearch className="h-6 w-6 text-gray-400" />
            </button>
          </form>
        </div>

        {/* === 右側使用者頭像區 === */}
        <div className="flex-1 flex justify-end items-center space-x-3 min-w-[160px]">
          <li
            className="relative list-none"
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
          >
            <button
              className="flex items-center space-x-2"
              onClick={() => setIsProfileOpen(!isProfileOpen)}
            >
              {/* 使用者名稱（固定寬度 + 省略 + 提示） */}
              <span
                className="hidden lg:inline text-gray-400 text-lg truncate max-w-[140px] inline-block align-middle"
                title={user?.profile?.display_name || ''}
              >
                {user ? user.profile?.display_name : '載入中...'}
              </span>

              {/* 頭像 */}
              <img
                className="h-10 w-10 rounded-full object-cover"
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
                  href="/profile?tab=watchlist"
                  onClick={() => setIsProfileOpen(false)}
                  className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  <FaHeart className="mr-2 h-5 w-5 text-gray-400" />
                  待看清單
                </Link>
                <Link
                  href="/profile?tab=lists"
                  onClick={() => setIsProfileOpen(false)}
                  className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  <FaListAlt className="mr-2 h-5 w-5 text-gray-400" />
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
      </nav>

      {/* === Logout Modal === */}
      <LogoutModal
        isOpen={isLogoutModalOpen}
        onClose={() => setIsLogoutModalOpen(false)}
        onConfirm={performLogout}
      />
    </>
  );
}
