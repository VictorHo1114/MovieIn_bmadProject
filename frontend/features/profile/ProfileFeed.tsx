"use client"
import { useState, useEffect } from "react"
import type React from "react"

import { useRouter, useSearchParams } from "next/navigation"
import { Api } from "../../lib/api"
import type { UserPublic } from "../../lib/types/user"
import ProfileEditorClient from '../../components/ProfileEditorClient';
import {
  FaUserCircle,
  FaHeart,
  FaListAlt,
  FaCog,
  FaSignOutAlt,
  FaMapMarkerAlt,
  FaEye,
  FaEyeSlash,
  FaTrophy,
  FaStar,
} from "react-icons/fa"
import { LogoutModal } from "../../components/LogoutModal"
import { WatchlistSection } from "./WatchlistSection"
import { Top10Section } from "./Top10Section"
import { EnhancedProfileEditor } from "../../components/profile/EnhancedProfileEditor"

export function ProfileFeed() {
  const router = useRouter()
  const searchParams = useSearchParams()

  // --- 狀態管理 ---
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [activeTab, setActiveTab] = useState("profile")
  const [isEditingProfile, setIsEditingProfile] = useState(false)

  const [user, setUser] = useState<UserPublic | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const [displayName, setDisplayName] = useState("")

  const [oldPassword, setOldPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [repeatPassword, setRepeatPassword] = useState("")

  const [showOldPassword, setShowOldPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showRepeatPassword, setShowRepeatPassword] = useState(false)

  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // --- 載入使用者資料 ---
  useEffect(() => {
    const fetchUser = async () => {
      const otherId = searchParams.get('id') || searchParams.get('user');
      try {
        if (otherId) {
          // Viewing another user's public profile
          const userData = await Api.profile.getById(otherId);
          setUser(userData);
          setDisplayName(userData.profile?.display_name || '');
          setIsLoading(false);
        } else {
          // Viewing own profile
          try {
            const userData = await Api.profile.me()
            setUser(userData)
            setDisplayName(userData.profile?.display_name || "")
          } catch (err) {
            console.error('Failed to fetch current user:', err);
            setError('無法載入個人資料，請重新登入。');
            localStorage.removeItem('authToken');
            router.push('/login');
            return;
          } finally {
            setIsLoading(false)
          }
        }
      } catch (error) {
        console.error("Failed to fetch user:", error)
        setError("無法載入個人資料，請重新登入。")
        localStorage.removeItem("authToken")
        router.push("/login")
      }
    }
    fetchUser()

    // 監聽積分更新事件
    const handlePointsUpdate = () => {
      fetchUser()
    }
    window.addEventListener("quizPointsUpdated", handlePointsUpdate)
    window.addEventListener("profileUpdated", handlePointsUpdate)

    return () => {
      window.removeEventListener("quizPointsUpdated", handlePointsUpdate)
      window.removeEventListener("profileUpdated", handlePointsUpdate)
    }
  }, [router])

  // --- 同步網址的 tab 參數 ---
  useEffect(() => {
    const tabFromUrl = searchParams.get("tab")
    const validTabs = ["profile", "watchlist", "lists", "settings"]
    if (tabFromUrl && validTabs.includes(tabFromUrl)) {
      setActiveTab(tabFromUrl)
    }
  }, [searchParams])

  // --- 判斷是否在檢視他人個人頁 ---
  const viewingOther = Boolean(searchParams.get('id') || searchParams.get('user'));

  // --- 修改名稱 ---
  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccessMessage(null)

    if (displayName === user?.profile?.display_name) {
      setError("您尚未修改顯示名稱。")
      return
    }

    try {
      const updatedUser = await Api.profile.updateMe({
        display_name: displayName,
      })
      setUser(updatedUser)
      setSuccessMessage("顯示名稱已成功更新！")

      // 廣播事件
      window.dispatchEvent(new CustomEvent("profileUpdated"))
    } catch (err: any) {
      console.error("Failed to update profile:", err)
      setError("儲存變更時發生錯誤，請再試一次。")
    }
  }

  // --- 修改密碼 ---
  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccessMessage(null)

    if (!oldPassword || !newPassword || !repeatPassword) {
      setError("請填寫所有密碼欄位。")
      return
    }
    if (newPassword !== repeatPassword) {
      setError("新密碼與確認密碼不一致。")
      return
    }
    if (newPassword.length < 8) {
      setError("新密碼至少需 8 個字元。")
      return
    }

    try {
      await Api.auth.changePassword({
        old_password: oldPassword,
        new_password: newPassword,
      })
      setSuccessMessage("密碼已成功變更！")
      setOldPassword("")
      setNewPassword("")
      setRepeatPassword("")
    } catch (err: any) {
      console.error("Failed to change password:", err)
      if (err.message && (err.message.includes("400") || err.message.includes("Incorrect"))) {
        setError("舊密碼不正確，請再試一次。")
      } else {
        setError("發生錯誤，請稍後再試。")
      }
    }
  }

  const performLogout = () => {
    localStorage.removeItem("authToken")
    setUser(null)
    console.log("User logged out")
    setIsModalOpen(false)
    router.push("/login")
  }

  // --- 載入中 ---
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-300 text-lg">載入個人資料中...</p>
        </div>
      </div>
    )
  }

  // --- 成功與錯誤提示 ---
  const renderAlerts = () => (
    <>
      {successMessage && (
        <div className="mb-6 p-4 text-sm bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg backdrop-blur-sm">
          {successMessage}
        </div>
      )}
      {error && (
        <div className="mb-6 p-4 text-sm bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg backdrop-blur-sm">
          {error}
        </div>
      )}
    </>
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <section className="relative overflow-hidden rounded-2xl mb-8 bg-gradient-to-r from-slate-800/80 via-slate-700/80 to-slate-800/80 backdrop-blur-xl border border-slate-700/50 shadow-2xl">
          {/* Decorative elements */}
          <div className="absolute inset-0 bg-[url('/film-grain-texture.png')] opacity-5 mix-blend-overlay"></div>
          <div className="absolute top-0 right-0 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl"></div>

          <div className="relative p-8 lg:p-12">
            <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-8">
              {/* 左側資訊 */}
              <div className="flex-1">
                <div className="flex items-center gap-4 mb-4">
                  <img
                    src={user?.profile?.avatar_url || '/img/default-avatar.jpg'}
                    alt={user?.profile?.display_name || '使用者'}
                    className="w-20 h-20 rounded-full object-cover border-4 border-amber-500/30 shadow-lg shadow-amber-500/20"
                  />
                  <div>
                    <h1 className="text-4xl font-bold text-white mb-1 tracking-tight">
                      {user?.profile?.display_name || "使用者"}
                    </h1>
                    <span className="text-slate-400 flex items-center gap-2 text-sm">
                      <FaMapMarkerAlt className="w-3 h-3" />
                      {user?.email}
                    </span>
                  </div>
                </div>

                {/* 積分與等級 */}
                <div className="flex gap-4 mt-6">
                  <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl px-6 py-4 border border-slate-700/50 hover:border-amber-500/30 transition-all duration-300">
                    <div className="flex items-center gap-2 mb-1">
                      <FaTrophy className="w-4 h-4 text-amber-400" />
                      <p className="text-xs text-slate-400 uppercase tracking-wider">總積分</p>
                    </div>
                    <p className="text-3xl font-bold text-amber-400">{user?.total_points || 0}</p>
                  </div>
                  <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl px-6 py-4 border border-slate-700/50 hover:border-emerald-500/30 transition-all duration-300">
                    <div className="flex items-center gap-2 mb-1">
                      <FaStar className="w-4 h-4 text-emerald-400" />
                      <p className="text-xs text-slate-400 uppercase tracking-wider">等級</p>
                    </div>
                    <p className="text-3xl font-bold text-emerald-400">LV.{user?.level || 1}</p>
                  </div>
                </div>
              </div>

              {/* 右側登出按鈕 */}
              <div>
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="px-6 py-3 bg-slate-700/50 hover:bg-slate-600/50 text-white font-medium rounded-xl border border-slate-600/50 hover:border-slate-500/50 transition-all duration-300 backdrop-blur-sm shadow-lg hover:shadow-xl"
                >
                  登出
                </button>
              </div>
            </div>
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* 左側導覽列 */}
          <div className="lg:col-span-1">
            <div className="bg-slate-800/60 backdrop-blur-xl rounded-xl border border-slate-700/50 p-2 shadow-xl sticky top-6">
              <nav className="flex flex-col gap-1">
                <button
                  onClick={() => setActiveTab("profile")}
                  className={`flex items-center gap-3 w-full text-left px-4 py-3 rounded-lg font-medium transition-all duration-300 ${
                    activeTab === "profile"
                      ? "bg-amber-500/20 text-amber-400 border border-amber-500/30 shadow-lg shadow-amber-500/10"
                      : "text-slate-400 hover:bg-slate-700/50 hover:text-slate-200"
                  }`}
                >
                  <FaUserCircle className="w-5 h-5" />
                  <span>個人資料</span>
                </button>

                <button
                  onClick={() => setActiveTab("watchlist")}
                  className={`flex items-center gap-3 w-full text-left px-4 py-3 rounded-lg font-medium transition-all duration-300 ${
                    activeTab === "watchlist"
                      ? "bg-amber-500/20 text-amber-400 border border-amber-500/30 shadow-lg shadow-amber-500/10"
                      : "text-slate-400 hover:bg-slate-700/50 hover:text-slate-200"
                  }`}
                >
                  <FaListAlt className="w-5 h-5" />
                  <span>待看清單</span>
                </button>

                <button
                  onClick={() => setActiveTab("lists")}
                  className={`flex items-center gap-3 w-full text-left px-4 py-3 rounded-lg font-medium transition-all duration-300 ${
                    activeTab === "lists"
                      ? "bg-amber-500/20 text-amber-400 border border-amber-500/30 shadow-lg shadow-amber-500/10"
                      : "text-slate-400 hover:bg-slate-700/50 hover:text-slate-200"
                  }`}
                >
                  <FaHeart className="w-5 h-5" />
                  <span>十大最愛</span>
                </button>

                <button
                  onClick={() => setActiveTab("settings")}
                  className={`flex items-center gap-3 w-full text-left px-4 py-3 rounded-lg font-medium transition-all duration-300 ${
                    activeTab === "settings"
                      ? "bg-amber-500/20 text-amber-400 border border-amber-500/30 shadow-lg shadow-amber-500/10"
                      : "text-slate-400 hover:bg-slate-700/50 hover:text-slate-200"
                  }`}
                >
                  <FaCog className="w-5 h-5" />
                  <span>帳戶設定</span>
                </button>

                <div className="my-2 border-t border-slate-700/50"></div>

                <button
                  onClick={() => setIsModalOpen(true)}
                  className="flex items-center gap-3 w-full text-left px-4 py-3 rounded-lg font-medium text-slate-500 hover:bg-slate-700/30 hover:text-slate-300 transition-all duration-300"
                >
                  <FaSignOutAlt className="w-5 h-5" />
                  <span>登出</span>
                </button>
              </nav>
            </div>
          </div>

          {/* 右側內容 */}
          <div className="lg:col-span-3">
            <div className="bg-slate-800/60 backdrop-blur-xl rounded-xl border border-slate-700/50 p-6 lg:p-8 shadow-xl">
              {/* 內容 1: 編輯個人資料 */}
              {activeTab === "profile" && (
                <div>
                  <div className="mb-6 pb-4 border-b border-slate-700/50 flex justify-between items-center">
                    <div>
                      <h2 className="text-2xl font-bold text-white">
                        {isEditingProfile ? "編輯個人資料" : "個人資料"}
                      </h2>
                      <p className="text-slate-400 text-sm mt-1">
                        {isEditingProfile ? "管理你的公開個人資訊與交友設定" : "查看你的個人資訊"}
                      </p>
                    </div>
                    {!isEditingProfile && (
                      <button
                        onClick={() => setIsEditingProfile(true)}
                        className="px-6 py-2.5 bg-amber-500 hover:bg-amber-600 text-white font-medium rounded-lg transition-all duration-300 shadow-lg shadow-amber-500/20 hover:shadow-xl hover:shadow-amber-500/30"
                      >
                        編輯資料
                      </button>
                    )}
                  </div>
                  
                  {isEditingProfile ? (
                    <div>
                      <EnhancedProfileEditor 
                        user={user} 
                        onUpdate={(updated) => {
                          setUser(updated);
                          setSuccessMessage("個人資料已更新！");
                          setIsEditingProfile(false);
                        }}
                        onCancel={() => setIsEditingProfile(false)}
                      />
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {renderAlerts()}
                      
                      {/* 個人資料預覽 */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* 顯示名稱 */}
                        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                          <label className="block text-sm font-medium text-slate-400 mb-2">顯示名稱</label>
                          <p className="text-white text-lg">{user?.profile?.display_name || "未設定"}</p>
                        </div>

                        {/* Email */}
                        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                          <label className="block text-sm font-medium text-slate-400 mb-2">電子郵件</label>
                          <p className="text-white text-lg">{user?.email}</p>
                        </div>

                        {/* 個人簡介 */}
                        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50 md:col-span-2">
                          <label className="block text-sm font-medium text-slate-400 mb-2">個人簡介</label>
                          <p className="text-white text-base whitespace-pre-wrap">
                            {user?.profile?.bio || "尚未填寫個人簡介"}
                          </p>
                        </div>

                        {/* 喜愛的類型 */}
                        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50 md:col-span-2">
                          <label className="block text-sm font-medium text-slate-400 mb-3">喜愛的電影類型</label>
                          {user?.profile?.favorite_genres && user.profile.favorite_genres.length > 0 ? (
                            <div className="flex flex-wrap gap-2">
                              {user.profile.favorite_genres.map((genre, index) => (
                                <span
                                  key={index}
                                  className="px-3 py-1.5 bg-amber-500/20 text-amber-400 rounded-lg text-sm border border-amber-500/30"
                                >
                                  {genre}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <p className="text-slate-500 text-sm">尚未選擇喜愛的電影類型</p>
                          )}
                        </div>

                        {/* 隱私設定 */}
                        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                          <label className="block text-sm font-medium text-slate-400 mb-2">隱私等級</label>
                          <p className="text-white text-lg capitalize">
                            {user?.profile?.privacy_level === "public" && "公開"}
                            {user?.profile?.privacy_level === "friends" && "僅好友"}
                            {user?.profile?.privacy_level === "private" && "私人"}
                            {!user?.profile?.privacy_level && "未設定"}
                          </p>
                        </div>

                        {/* 成人內容偏好 */}
                        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                          <label className="block text-sm font-medium text-slate-400 mb-2">成人內容</label>
                          <p className="text-white text-lg">
                            {user?.profile?.adult_content_opt_in ? "已啟用" : "已停用"}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* 內容 2: 我的追蹤 */}
              {activeTab === "watchlist" && (
                <div>
                  <div className="mb-6 pb-4 border-b border-slate-700/50">
                    <h2 className="text-2xl font-bold text-white">待看清單</h2>
                    <p className="text-slate-400 text-sm mt-1">你想看的所有電影</p>
                  </div>
                  <WatchlistSection />
                </div>
              )}

              {/* 內容 3: 我的清單 */}
              {activeTab === "lists" && (
                <div>
                  <div className="mb-6 pb-4 border-b border-slate-700/50">
                    <h2 className="text-2xl font-bold text-white">我的十大片單</h2>
                    <p className="text-slate-400 text-sm mt-1">你最喜愛的電影排行榜</p>
                  </div>
                  <Top10Section />
                </div>
              )}

              {/* 內容 4: 帳號設定 (修改密碼) */}
              {activeTab === "settings" && (
                <div>
                  <div className="mb-6 pb-4 border-b border-slate-700/50">
                    <h2 className="text-2xl font-bold text-white">帳戶設定</h2>
                    <p className="text-slate-400 text-sm mt-1">管理你的帳戶安全</p>
                  </div>
                  {renderAlerts()}
                  <form onSubmit={handlePasswordChange} className="space-y-6">
                    {/* 舊密碼 */}
                    <div>
                      <label htmlFor="oldPassword" className="block text-sm font-medium text-slate-300 mb-2">
                        舊密碼
                      </label>
                      <div className="relative">
                        <input
                          id="oldPassword"
                          type={showOldPassword ? "text" : "password"}
                          className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-3 pr-12 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500/50 transition-all"
                          placeholder="輸入目前的密碼"
                          value={oldPassword}
                          onChange={(e) => {
                            setOldPassword(e.target.value)
                            setError(null)
                            setSuccessMessage(null)
                          }}
                        />
                        <button
                          type="button"
                          onClick={() => setShowOldPassword(!showOldPassword)}
                          className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300 transition-colors"
                        >
                          {showOldPassword ? <FaEyeSlash className="w-5 h-5" /> : <FaEye className="w-5 h-5" />}
                        </button>
                      </div>
                    </div>

                    {/* 新密碼與再次輸入新密碼 */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* 新密碼 */}
                      <div>
                        <label htmlFor="newPassword" className="block text-sm font-medium text-slate-300 mb-2">
                          新密碼
                        </label>
                        <div className="relative">
                          <input
                            id="newPassword"
                            type={showNewPassword ? "text" : "password"}
                            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-3 pr-12 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500/50 transition-all"
                            placeholder="新密碼（至少 8 個字元）"
                            value={newPassword}
                            onChange={(e) => {
                              setNewPassword(e.target.value)
                              setError(null)
                              setSuccessMessage(null)
                            }}
                          />
                          <button
                            type="button"
                            onClick={() => setShowNewPassword(!showNewPassword)}
                            className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300 transition-colors"
                          >
                            {showNewPassword ? <FaEyeSlash className="w-5 h-5" /> : <FaEye className="w-5 h-5" />}
                          </button>
                        </div>
                      </div>

                      {/* 再次輸入新密碼 */}
                      <div>
                        <label htmlFor="repeatPassword" className="block text-sm font-medium text-slate-300 mb-2">
                          再次輸入新密碼
                        </label>
                        <div className="relative">
                          <input
                            id="repeatPassword"
                            type={showRepeatPassword ? "text" : "password"}
                            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-3 pr-12 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500/50 transition-all"
                            placeholder="再次輸入新密碼"
                            value={repeatPassword}
                            onChange={(e) => {
                              setRepeatPassword(e.target.value)
                              setError(null)
                              setSuccessMessage(null)
                            }}
                          />
                          <button
                            type="button"
                            onClick={() => setShowRepeatPassword(!showRepeatPassword)}
                            className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300 transition-colors"
                          >
                            {showRepeatPassword ? <FaEyeSlash className="w-5 h-5" /> : <FaEye className="w-5 h-5" />}
                          </button>
                        </div>
                      </div>
                    </div>

                    <div className="pt-4">
                      <button
                        type="submit"
                        className="px-6 py-3 bg-amber-500 hover:bg-amber-600 text-white font-medium rounded-lg transition-all duration-300 shadow-lg shadow-amber-500/20 hover:shadow-xl hover:shadow-amber-500/30"
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
      </div>

      <LogoutModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onConfirm={performLogout} />
    </div>
  )
}
