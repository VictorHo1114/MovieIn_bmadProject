'use client';
import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Api } from '../../lib/api';
import { UserPublic } from '../../lib/types/user';
import {
  FaUserCircle,
  FaHeart,
  FaListAlt,
  FaCog,  
  FaSignOutAlt,
  FaMapMarkerAlt,
  FaEye,         // [新增！]
  FaEyeSlash     // [新增！]
} from 'react-icons/fa';
import { LogoutModal } from '../../components/LogoutModal';

export function ProfileFeed() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // --- 狀態管理 ---
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');

  const [user, setUser] = useState<UserPublic | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const [displayName, setDisplayName] = useState('');

  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [repeatPassword, setRepeatPassword] = useState('');

  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showRepeatPassword, setShowRepeatPassword] = useState(false);

  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // --- 載入使用者資料 ---
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userData = await Api.profile.me();
        setUser(userData);
        setDisplayName(userData.profile?.display_name || '');
        setIsLoading(false);
      } catch (error) {
        console.error('Failed to fetch user:', error);
        setError('無法載入個人資料，請重新登入。');
        localStorage.removeItem('authToken');
        router.push('/login');
      }
    };
    fetchUser();
  }, [router]);

  // --- 同步網址的 tab 參數 ---
  useEffect(() => {
    const tabFromUrl = searchParams.get('tab');
    const validTabs = ['profile', 'watchlist', 'lists', 'settings'];
    if (tabFromUrl && validTabs.includes(tabFromUrl)) {
      setActiveTab(tabFromUrl);
    }
  }, [searchParams]);

  // --- 修改名稱 ---
  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (displayName === user?.profile?.display_name) {
      setError('您尚未修改顯示名稱。');
      return;
    }

    try {
      const updatedUser = await Api.profile.updateMe({
        display_name: displayName,
      });
      setUser(updatedUser);
      setSuccessMessage('顯示名稱已成功更新！');

      // 廣播事件
      window.dispatchEvent(new CustomEvent('profileUpdated'));
    } catch (err: any) {
      console.error('Failed to update profile:', err);
      setError('儲存變更時發生錯誤，請再試一次。');
    }
  };

  // --- 修改密碼 ---
  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!oldPassword || !newPassword || !repeatPassword) {
      setError('請填寫所有密碼欄位。');
      return;
    }
    if (newPassword !== repeatPassword) {
      setError('新密碼與確認密碼不一致。');
      return;
    }
    if (newPassword.length < 8) {
      setError('新密碼至少需 8 個字元。');
      return;
    }

    try {
      await Api.auth.changePassword({
        old_password: oldPassword,
        new_password: newPassword,
      });
      setSuccessMessage('密碼已成功變更！');
      setOldPassword('');
      setNewPassword('');
      setRepeatPassword('');
    } catch (err: any) {
      console.error('Failed to change password:', err);
      if (err.message && (err.message.includes('400') || err.message.includes('Incorrect'))) {
        setError('舊密碼不正確，請再試一次。');
      } else {
        setError('發生錯誤，請稍後再試。');
      }
    }
  };

  const performLogout = () => {
    localStorage.removeItem('authToken');
    setUser(null);
    console.log('User logged out');
    setIsModalOpen(false);
    router.push('/login');
  };

  // --- 載入中 ---
  if (isLoading) {
    return <div className="p-10">載入個人資料中...</div>;
  }

  // --- 成功與錯誤提示 ---
  const renderAlerts = () => (
    <>
      {successMessage && (
        <div className="mb-4 p-4 text-sm text-green-700 bg-green-100 rounded-lg">
          {successMessage}
        </div>
      )}
      {error && (
        <div className="mb-4 p-4 text-sm text-red-700 bg-red-100 rounded-lg">
          {error}
        </div>
      )}
    </>
  );

  return (
    <div className="w-full mx-auto px-12 py-21 min-h-screen">
      {/* --- 頂部橫幅 --- */}
      <section className="p-4 bg-gradient-to-r from-blue-600 to-purple-700 text-white rounded-lg shadow-lg mb-4">
        <div className="flex flex-col md:flex-row justify-between items-center">
          {/* 左側資訊 */}
          <div className="text-left">
            <h1 className="text-3xl font-bold mb-1">
              {user?.profile?.display_name || '使用者'}
            </h1>
            <span className="text-gray-300 flex items-center">
              <FaMapMarkerAlt className="inline-block h-4 w-4" />
              <span className="ml-1">{user?.email}</span>
            </span>
          </div>
          {/* 右側登出按鈕 */}
          <div className="text-right mt-4 md:mt-0">
            <button
              onClick={() => setIsModalOpen(true)}
              className="bg-white text-gray-800 font-bold p-3 rounded-lg shadow hover:bg-gray-200"
            >
              登出
            </button>
          </div>
        </div>
      </section>

      {/* --- 主體兩欄佈局 --- */}
      <div className="flex flex-wrap -mx-4">
        {/* 左側導覽列 */}
        <div className="w-full lg:w-1/4 px-4">
          <div className="bg-white p-3 shadow rounded-lg mb-4">
            <div className="flex flex-col space-y-1">
              <button
                onClick={() => setActiveTab('profile')}
                className={`flex items-center w-full text-left pl-2 py-2 rounded ${
                  activeTab === 'profile'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <FaUserCircle className="mr-2" /> 個人資料
              </button>

              <button
                onClick={() => setActiveTab('watchlist')}
                className={`flex items-center w-full text-left px-1 py-2 rounded ${
                  activeTab === 'watchlist'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <FaHeart className="mr-2" /> 待看清單
              </button>

              <button
                onClick={() => setActiveTab('lists')}
                className={`flex items-center w-full text-left pl-1 py-2 rounded ${
                  activeTab === 'lists'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <FaListAlt className="mr-2" /> 我的片單
              </button>

              <button
                onClick={() => setActiveTab('settings')}
                className={`flex items-center w-full text-left pl-2 py-2 rounded ${
                  activeTab === 'settings'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <FaCog className="mr-2" /> 帳戶設定
              </button>

              <button
                onClick={() => setIsModalOpen(true)}
                className="flex items-center w-full text-left pl-2 py-2 rounded text-gray-500 hover:bg-gray-100"
              >
                <FaSignOutAlt className="mr-2" /> 登出
              </button>
            </div>
          </div>
        </div>

        {/* 右側內容 */}
        <div className="w-full lg:w-3/4 px-4">
          <div className="bg-white p-5 widget shadow rounded-lg mb-4">
            {/* 內容 1: 編輯個人資料 */}
            {activeTab === 'profile' && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h1 className="text-xl font-bold text-gray-900">編輯個人資料</h1>
                </div>
                {renderAlerts()}
                <form
                  onSubmit={handleProfileUpdate}
                  className="grid grid-cols-1 md:grid-cols-2 gap-4"
                >
                  <div className="md:col-span-2">
                    <label
                      htmlFor="displayName"
                      className="block text-sm font-medium text-gray-700"
                    >
                      顯示名稱
                    </label>
                    <input
                      id="displayName"
                      type="text"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900"
                      placeholder="輸入公開顯示的名稱"
                      value={displayName}
                      onChange={(e) => {
                        setDisplayName(e.target.value);
                        setError(null);
                        setSuccessMessage(null);
                      }}
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label
                      htmlFor="email"
                      className="block text-sm font-medium text-gray-700"
                    >
                      電子郵件
                    </label>
                    <input
                      id="email"
                      type="email"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 bg-gray-100 text-gray-400"
                      value={user?.email || ''}
                      disabled
                    />
                  </div>

                  <div className="md:col-span-2 text-left">
                    <button
                      type="submit"
                      className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                    >
                      儲存變更
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* 內容 2: 我的追蹤 */}
            {activeTab === 'watchlist' && (
              <div>
                <h1 className="text-xl font-bold text-gray-900">待看清單</h1>
                <p className="p-4">功能開發中...</p>
              </div>
            )}

            {/* 內容 3: 我的清單 */}
            {activeTab === 'lists' && (
              <div>
                <h1 className="text-xl font-bold text-gray-900">我的片單</h1>
                <p className="p-4">功能開發中...</p>
              </div>
            )}

            {/* 內容 4: 帳號設定 (修改密碼) */}
            {activeTab === 'settings' && (
  <div>
    <div className="flex items-center justify-between mb-3">
      <h1 className="text-xl font-bold text-gray-900">帳戶設定</h1>
    </div>
    {renderAlerts()}
    <form onSubmit={handlePasswordChange} className="grid grid-cols-1 gap-4">

      {/* 舊密碼 */}
      <div className="relative">
        <label
          htmlFor="oldPassword"
          className="block text-sm font-medium text-gray-700"
        >
          舊密碼
        </label>
        <div className="relative mt-1">
          <input
            id="oldPassword"
            type={showOldPassword ? 'text' : 'password'}
            className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 pr-10 text-gray-900 placeholder-gray-400 focus:ring-blue-500 focus:border-blue-500"
            placeholder="輸入目前的密碼"
            value={oldPassword}
            onChange={(e) => {
              setOldPassword(e.target.value);
              setError(null);
              setSuccessMessage(null);
            }}
          />
          <button
            type="button"
            onClick={() => setShowOldPassword(!showOldPassword)}
            className="absolute top-1/2 right-3 -translate-y-1/2 text-gray-400 hover:text-gray-600 focus:outline-none"
          >
            {showOldPassword ? (
              <FaEyeSlash className="h-5 w-5" />
            ) : (
              <FaEye className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>

      {/* 新密碼與再次輸入新密碼 */}
      <div className="flex flex-col sm:flex-row sm:space-x-4 space-y-4 sm:space-y-0">

        {/* 新密碼 */}
        <div className="sm:w-1/2 relative">
          <label
            htmlFor="newPassword"
            className="block text-sm font-medium text-gray-700"
          >
            新密碼
          </label>
          <div className="relative mt-1">
            <input
              id="newPassword"
              type={showNewPassword ? 'text' : 'password'}
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 pr-10 text-gray-900 placeholder-gray-400 focus:ring-blue-500 focus:border-blue-500"
              placeholder="新密碼（至少 8 個字元）"
              value={newPassword}
              onChange={(e) => {
                setNewPassword(e.target.value);
                setError(null);
                setSuccessMessage(null);
              }}
            />
            <button
              type="button"
              onClick={() => setShowNewPassword(!showNewPassword)}
              className="absolute top-1/2 right-3 -translate-y-1/2 text-gray-400 hover:text-gray-600 focus:outline-none"
            >
              {showNewPassword ? (
                <FaEyeSlash className="h-5 w-5" />
              ) : (
                <FaEye className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>

        {/* 再次輸入新密碼 */}
        <div className="sm:w-1/2 relative">
          <label
            htmlFor="repeatPassword"
            className="block text-sm font-medium text-gray-700"
          >
            再次輸入新密碼
          </label>
          <div className="relative mt-1">
            <input
              id="repeatPassword"
              type={showRepeatPassword ? 'text' : 'password'}
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 pr-10 text-gray-900 placeholder-gray-400 focus:ring-blue-500 focus:border-blue-500"
              placeholder="再次輸入新密碼"
              value={repeatPassword}
              onChange={(e) => {
                setRepeatPassword(e.target.value);
                setError(null);
                setSuccessMessage(null);
              }}
            />
            <button
              type="button"
              onClick={() => setShowRepeatPassword(!showRepeatPassword)}
              className="absolute top-1/2 right-3 -translate-y-1/2 text-gray-400 hover:text-gray-600 focus:outline-none"
            >
              {showRepeatPassword ? (
                <FaEyeSlash className="h-5 w-5" />
              ) : (
                <FaEye className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="text-left">
        <button
          type="submit"
          className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          儲存密碼
        </button>
      </div>
    </form>
  </div>
)}

          </div>
        </div>
      </div>

      <LogoutModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={performLogout}
      />
    </div>
  );
}
