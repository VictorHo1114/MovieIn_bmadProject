"use client"
import { useState, useEffect } from "react"
import type React from "react"
import { useRouter, useSearchParams } from "next/navigation"
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
  FaFilm,
  FaTicketAlt,
} from "react-icons/fa"

type UserPublic = {
  email: string
  profile?: {
    display_name: string
  }
  total_points: number
  level: number
}

const MockApi = {
  profile: {
    me: async (): Promise<UserPublic> => ({
      email: "user@example.com",
      profile: { display_name: "電影愛好者" },
      total_points: 2450,
      level: 5,
    }),
    updateMe: async (data: any): Promise<UserPublic> => ({
      email: "user@example.com",
      profile: { display_name: data.display_name },
      total_points: 2450,
      level: 5,
    }),
  },
  auth: {
    changePassword: async (data: any) => {
      return { success: true }
    },
  },
}

function LogoutModal({ isOpen, onClose, onConfirm }: any) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md">
      <div
        className="relative bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8 max-w-md w-full mx-4 border-2 border-primary/30 shadow-2xl shadow-primary/20 overflow-hidden"
        style={{
          clipPath: "polygon(0 0, calc(100% - 20px) 0, 100% 20px, 100% 100%, 20px 100%, 0 calc(100% - 20px))",
        }}
      >
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-32 h-32 bg-accent/5 blur-3xl" />

        <div className="relative">
          <div className="flex items-center gap-3 mb-6">
            <FaTicketAlt className="w-8 h-8 text-primary" />
            <h2 className="text-3xl font-bold text-foreground tracking-tight">確認登出</h2>
          </div>
          <p className="text-muted-foreground text-lg mb-8 leading-relaxed">確定要結束本次觀影嗎？</p>
          <div className="flex gap-4">
            <button
              onClick={onClose}
              className="flex-1 px-6 py-4 bg-secondary/50 text-secondary-foreground rounded-lg hover:bg-secondary/70 transition-all duration-300 font-semibold text-lg border border-border/50"
            >
              取消
            </button>
            <button
              onClick={onConfirm}
              className="flex-1 px-6 py-4 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-all duration-300 font-semibold text-lg shadow-lg shadow-primary/30"
            >
              確定登出
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function WatchlistSection() {
  return (
    <div className="text-center py-32">
      <div className="mb-6 inline-block p-6 bg-muted/30 rounded-full border-2 border-dashed border-muted-foreground/20">
        <FaFilm className="w-16 h-16 text-muted-foreground/40" />
      </div>
      <p className="text-2xl text-foreground/80 mb-3 font-semibold">你的待看清單是空的</p>
      <p className="text-base text-muted-foreground max-w-md mx-auto leading-relaxed">
        點擊電影卡片的「加入 Watchlist」按鈕來新增電影
      </p>
    </div>
  )
}

function Top10Section() {
  return (
    <div className="text-center py-32">
      <div className="mb-6 inline-block p-6 bg-muted/30 rounded-full border-2 border-dashed border-muted-foreground/20">
        <FaTrophy className="w-16 h-16 text-muted-foreground/40" />
      </div>
      <p className="text-2xl text-foreground/80 mb-3 font-semibold">你的 Top 10 清單是空的</p>
      <p className="text-base text-muted-foreground max-w-md mx-auto leading-relaxed">
        點擊電影卡片的「加入 Top 10 List」按鈕來新增電影（最多 10 部）
      </p>
    </div>
  )
}

export default function ProfilePage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [activeTab, setActiveTab] = useState("profile")

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

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userData = await MockApi.profile.me()
        setUser(userData)
        setDisplayName(userData.profile?.display_name || "")
        setIsLoading(false)
      } catch (error) {
        console.error("Failed to fetch user:", error)
        setError("無法載入個人資料，請重新登入。")
      }
    }
    fetchUser()
  }, [router])

  useEffect(() => {
    const tabFromUrl = searchParams.get("tab")
    const validTabs = ["profile", "watchlist", "lists", "settings"]
    if (tabFromUrl && validTabs.includes(tabFromUrl)) {
      setActiveTab(tabFromUrl)
    }
  }, [searchParams])

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccessMessage(null)

    if (displayName === user?.profile?.display_name) {
      setError("您尚未修改顯示名稱。")
      return
    }

    try {
      const updatedUser = await MockApi.profile.updateMe({
        display_name: displayName,
      })
      setUser(updatedUser)
      setSuccessMessage("顯示名稱已成功更新！")
    } catch (err: any) {
      console.error("Failed to update profile:", err)
      setError("儲存變更時發生錯誤，請再試一次。")
    }
  }

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
      await MockApi.auth.changePassword({
        old_password: oldPassword,
        new_password: newPassword,
      })
      setSuccessMessage("密碼已成功變更！")
      setOldPassword("")
      setNewPassword("")
      setRepeatPassword("")
    } catch (err: any) {
      console.error("Failed to change password:", err)
      setError("發生錯誤，請稍後再試。")
    }
  }

  const performLogout = () => {
    setUser(null)
    console.log("User logged out")
    setIsModalOpen(false)
    router.push("/login")
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-20 h-20 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
          <p className="text-muted-foreground text-xl font-medium">載入個人資料中...</p>
        </div>
      </div>
    )
  }

  const renderAlerts = () => (
    <>
      {successMessage && (
        <div className="mb-6 p-5 text-base text-emerald-200 bg-emerald-950/40 border-l-4 border-emerald-500 rounded-r-lg backdrop-blur-sm">
          {successMessage}
        </div>
      )}
      {error && (
        <div className="mb-6 p-5 text-base text-red-200 bg-red-950/40 border-l-4 border-red-500 rounded-r-lg backdrop-blur-sm">
          {error}
        </div>
      )}
    </>
  )

  return (
    <div className="min-h-screen bg-background">
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-accent/10 pointer-events-none" />

        <section className="relative px-6 py-12 lg:py-16">
          <div className="max-w-7xl mx-auto">
            {/* Bento Grid Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8">
              {/* Left Column - User Profile Card (Ticket Style) */}
              <div
                className="lg:col-span-5 relative overflow-hidden bg-gradient-to-br from-card via-card/95 to-card/90 border-2 border-primary/20 shadow-2xl shadow-primary/10"
                style={{
                  clipPath: "polygon(0 0, calc(100% - 30px) 0, 100% 30px, 100% 100%, 30px 100%, 0 calc(100% - 30px))",
                }}
              >
                <div className="absolute top-0 right-0 w-48 h-48 bg-primary/10 blur-3xl" />
                <div className="absolute bottom-0 left-0 w-48 h-48 bg-accent/10 blur-3xl" />

                <div className="relative p-8 lg:p-10">
                  <div className="flex items-start gap-5 mb-8">
                    <div className="relative">
                      <div className="w-24 h-24 lg:w-28 lg:h-28 rounded-2xl bg-gradient-to-br from-primary via-accent to-primary/80 flex items-center justify-center text-4xl lg:text-5xl font-black text-primary-foreground shadow-2xl shadow-primary/30 border-4 border-primary/30">
                        {user?.profile?.display_name?.[0] || "U"}
                      </div>
                      <div className="absolute -bottom-2 -right-2 w-10 h-10 bg-accent rounded-full border-4 border-card flex items-center justify-center">
                        <FaStar className="w-5 h-5 text-accent-foreground" />
                      </div>
                    </div>

                    <div className="flex-1">
                      <h1 className="text-4xl lg:text-5xl font-black text-foreground mb-2 tracking-tight leading-none">
                        {user?.profile?.display_name || "使用者"}
                      </h1>
                      <span className="text-muted-foreground flex items-center gap-2 text-sm lg:text-base">
                        <FaMapMarkerAlt className="w-4 h-4" />
                        {user?.email}
                      </span>
                    </div>
                  </div>

                  {/* Decorative ticket perforation */}
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-px border-t-2 border-dashed border-border/30" />
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 bg-background rounded-full border-2 border-border/30" />
                  <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 w-8 h-8 bg-background rounded-full border-2 border-border/30" />

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-4 mt-8">
                    <div className="bg-gradient-to-br from-primary/20 to-primary/5 backdrop-blur-sm border border-primary/30 rounded-xl p-5 shadow-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <FaStar className="w-5 h-5 text-primary" />
                        <p className="text-xs text-muted-foreground uppercase tracking-widest font-bold">總積分</p>
                      </div>
                      <p className="text-4xl font-black text-primary">{user?.total_points || 0}</p>
                    </div>
                    <div className="bg-gradient-to-br from-accent/20 to-accent/5 backdrop-blur-sm border border-accent/30 rounded-xl p-5 shadow-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <FaTrophy className="w-5 h-5 text-accent" />
                        <p className="text-xs text-muted-foreground uppercase tracking-widest font-bold">等級</p>
                      </div>
                      <p className="text-4xl font-black text-accent">LV.{user?.level || 1}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column - Action Cards */}
              <div className="lg:col-span-7 grid grid-cols-2 gap-4 lg:gap-6">
                {/* Quick Action Card 1 */}
                <div
                  onClick={() => setActiveTab("watchlist")}
                  className="col-span-2 lg:col-span-1 bg-gradient-to-br from-card to-card/80 border-2 border-border hover:border-primary/50 rounded-2xl p-6 lg:p-8 cursor-pointer transition-all duration-300 hover:shadow-2xl hover:shadow-primary/20 hover:-translate-y-1 group"
                >
                  <FaListAlt className="w-12 h-12 lg:w-14 lg:h-14 text-primary mb-4 group-hover:scale-110 transition-transform duration-300" />
                  <h3 className="text-2xl lg:text-3xl font-black text-foreground mb-2 tracking-tight">待看清單</h3>
                  <p className="text-muted-foreground text-sm lg:text-base leading-relaxed">管理你想看的電影</p>
                </div>

                {/* Quick Action Card 2 */}
                <div
                  onClick={() => setActiveTab("lists")}
                  className="col-span-2 lg:col-span-1 bg-gradient-to-br from-card to-card/80 border-2 border-border hover:border-accent/50 rounded-2xl p-6 lg:p-8 cursor-pointer transition-all duration-300 hover:shadow-2xl hover:shadow-accent/20 hover:-translate-y-1 group"
                >
                  <FaHeart className="w-12 h-12 lg:w-14 lg:h-14 text-accent mb-4 group-hover:scale-110 transition-transform duration-300" />
                  <h3 className="text-2xl lg:text-3xl font-black text-foreground mb-2 tracking-tight">十大最愛</h3>
                  <p className="text-muted-foreground text-sm lg:text-base leading-relaxed">展示你的最愛電影</p>
                </div>

                {/* Wide Action Card */}
                <div
                  onClick={() => setActiveTab("settings")}
                  className="col-span-2 bg-gradient-to-r from-secondary via-secondary/95 to-secondary/90 border-2 border-border hover:border-primary/50 rounded-2xl p-6 lg:p-8 cursor-pointer transition-all duration-300 hover:shadow-2xl hover:shadow-primary/20 hover:-translate-y-1 flex items-center justify-between group"
                >
                  <div>
                    <h3 className="text-2xl lg:text-3xl font-black text-secondary-foreground mb-2 tracking-tight">
                      帳戶設定
                    </h3>
                    <p className="text-secondary-foreground/70 text-sm lg:text-base leading-relaxed">
                      更新個人資料與密碼
                    </p>
                  </div>
                  <FaCog className="w-12 h-12 lg:w-14 lg:h-14 text-secondary-foreground/70 group-hover:rotate-90 transition-transform duration-500" />
                </div>

                {/* Logout Button */}
                <div className="col-span-2">
                  <button
                    onClick={() => setIsModalOpen(true)}
                    className="w-full px-6 py-5 bg-destructive/90 hover:bg-destructive border-2 border-destructive-foreground/20 text-destructive-foreground font-bold text-lg rounded-xl shadow-lg shadow-destructive/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-destructive/40 flex items-center justify-center gap-3"
                  >
                    <FaSignOutAlt className="w-6 h-6" />
                    登出帳號
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left sidebar navigation - Modern pill style */}
          <div className="lg:col-span-3">
            <div className="bg-card/50 backdrop-blur-sm border-2 border-border rounded-2xl p-3 shadow-xl sticky top-6">
              <nav className="flex flex-col gap-2">
                <button
                  onClick={() => setActiveTab("profile")}
                  className={`flex items-center gap-4 w-full text-left px-5 py-4 rounded-xl font-bold text-base transition-all duration-300 ${
                    activeTab === "profile"
                      ? "bg-primary text-primary-foreground shadow-lg shadow-primary/30 scale-105"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  }`}
                >
                  <FaUserCircle className="w-6 h-6" />
                  <span>個人資料</span>
                </button>

                <button
                  onClick={() => setActiveTab("watchlist")}
                  className={`flex items-center gap-4 w-full text-left px-5 py-4 rounded-xl font-bold text-base transition-all duration-300 ${
                    activeTab === "watchlist"
                      ? "bg-primary text-primary-foreground shadow-lg shadow-primary/30 scale-105"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  }`}
                >
                  <FaListAlt className="w-6 h-6" />
                  <span>待看清單</span>
                </button>

                <button
                  onClick={() => setActiveTab("lists")}
                  className={`flex items-center gap-4 w-full text-left px-5 py-4 rounded-xl font-bold text-base transition-all duration-300 ${
                    activeTab === "lists"
                      ? "bg-primary text-primary-foreground shadow-lg shadow-primary/30 scale-105"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  }`}
                >
                  <FaHeart className="w-6 h-6" />
                  <span>十大最愛</span>
                </button>

                <button
                  onClick={() => setActiveTab("settings")}
                  className={`flex items-center gap-4 w-full text-left px-5 py-4 rounded-xl font-bold text-base transition-all duration-300 ${
                    activeTab === "settings"
                      ? "bg-primary text-primary-foreground shadow-lg shadow-primary/30 scale-105"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  }`}
                >
                  <FaCog className="w-6 h-6" />
                  <span>帳戶設定</span>
                </button>

                <div className="h-px bg-border my-2" />

                <button
                  onClick={() => setIsModalOpen(true)}
                  className="flex items-center gap-4 w-full text-left px-5 py-4 rounded-xl font-bold text-base text-destructive-foreground bg-destructive/20 hover:bg-destructive/30 transition-all duration-300"
                >
                  <FaSignOutAlt className="w-6 h-6" />
                  <span>登出</span>
                </button>
              </nav>
            </div>
          </div>

          {/* Right content area */}
          <div className="lg:col-span-9">
            <div className="bg-card/70 backdrop-blur-md border-2 border-border rounded-2xl p-8 lg:p-10 shadow-2xl">
              {/* Profile tab */}
              {activeTab === "profile" && (
                <div>
                  <div className="flex items-center gap-4 mb-8">
                    <div className="w-2 h-12 bg-primary rounded-full" />
                    <h2 className="text-4xl font-black text-foreground tracking-tight">編輯個人資料</h2>
                  </div>
                  {renderAlerts()}
                  <form onSubmit={handleProfileUpdate} className="space-y-8">
                    <div>
                      <label htmlFor="displayName" className="block text-base font-bold text-foreground mb-3">
                        顯示名稱
                      </label>
                      <input
                        id="displayName"
                        type="text"
                        className="w-full bg-input/50 border-2 border-border focus:border-primary rounded-xl px-5 py-4 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-4 focus:ring-primary/20 transition-all text-lg font-medium"
                        placeholder="輸入公開顯示的名稱"
                        value={displayName}
                        onChange={(e) => {
                          setDisplayName(e.target.value)
                          setError(null)
                          setSuccessMessage(null)
                        }}
                      />
                    </div>

                    <div>
                      <label htmlFor="email" className="block text-base font-bold text-foreground mb-3">
                        電子郵件
                      </label>
                      <input
                        id="email"
                        type="email"
                        className="w-full bg-muted/30 border-2 border-border/50 rounded-xl px-5 py-4 text-muted-foreground cursor-not-allowed text-lg font-medium"
                        value={user?.email || ""}
                        disabled
                      />
                    </div>

                    <button
                      type="submit"
                      className="px-8 py-4 bg-primary hover:bg-primary/90 text-primary-foreground font-bold text-lg rounded-xl shadow-xl shadow-primary/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-primary/40"
                    >
                      儲存變更
                    </button>
                  </form>
                </div>
              )}

              {/* Watchlist tab */}
              {activeTab === "watchlist" && (
                <div>
                  <div className="flex items-center gap-4 mb-8">
                    <div className="w-2 h-12 bg-primary rounded-full" />
                    <h2 className="text-4xl font-black text-foreground tracking-tight">待看清單</h2>
                  </div>
                  <WatchlistSection />
                </div>
              )}

              {/* Top 10 tab */}
              {activeTab === "lists" && (
                <div>
                  <div className="flex items-center gap-4 mb-8">
                    <div className="w-2 h-12 bg-primary rounded-full" />
                    <h2 className="text-4xl font-black text-foreground tracking-tight">我的十大片單</h2>
                  </div>
                  <Top10Section />
                </div>
              )}

              {/* Settings tab */}
              {activeTab === "settings" && (
                <div>
                  <div className="flex items-center gap-4 mb-8">
                    <div className="w-2 h-12 bg-primary rounded-full" />
                    <h2 className="text-4xl font-black text-foreground tracking-tight">帳戶設定</h2>
                  </div>
                  {renderAlerts()}
                  <form onSubmit={handlePasswordChange} className="space-y-8">
                    <div>
                      <label htmlFor="oldPassword" className="block text-base font-bold text-foreground mb-3">
                        舊密碼
                      </label>
                      <div className="relative">
                        <input
                          id="oldPassword"
                          type={showOldPassword ? "text" : "password"}
                          className="w-full bg-input/50 border-2 border-border focus:border-primary rounded-xl px-5 py-4 pr-14 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-4 focus:ring-primary/20 transition-all text-lg font-medium"
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
                          className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                        >
                          {showOldPassword ? <FaEyeSlash className="w-6 h-6" /> : <FaEye className="w-6 h-6" />}
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label htmlFor="newPassword" className="block text-base font-bold text-foreground mb-3">
                          新密碼
                        </label>
                        <div className="relative">
                          <input
                            id="newPassword"
                            type={showNewPassword ? "text" : "password"}
                            className="w-full bg-input/50 border-2 border-border focus:border-primary rounded-xl px-5 py-4 pr-14 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-4 focus:ring-primary/20 transition-all text-lg font-medium"
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
                            className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                          >
                            {showNewPassword ? <FaEyeSlash className="w-6 h-6" /> : <FaEye className="w-6 h-6" />}
                          </button>
                        </div>
                      </div>

                      <div>
                        <label htmlFor="repeatPassword" className="block text-base font-bold text-foreground mb-3">
                          再次輸入新密碼
                        </label>
                        <div className="relative">
                          <input
                            id="repeatPassword"
                            type={showRepeatPassword ? "text" : "password"}
                            className="w-full bg-input/50 border-2 border-border focus:border-primary rounded-xl px-5 py-4 pr-14 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-4 focus:ring-primary/20 transition-all text-lg font-medium"
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
                            className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                          >
                            {showRepeatPassword ? <FaEyeSlash className="w-6 h-6" /> : <FaEye className="w-6 h-6" />}
                          </button>
                        </div>
                      </div>
                    </div>

                    <button
                      type="submit"
                      className="px-8 py-4 bg-primary hover:bg-primary/90 text-primary-foreground font-bold text-lg rounded-xl shadow-xl shadow-primary/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-primary/40"
                    >
                      儲存密碼
                    </button>
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
