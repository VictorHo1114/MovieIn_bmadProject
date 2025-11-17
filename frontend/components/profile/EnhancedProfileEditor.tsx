"use client";

import { useState, useEffect } from "react";
import { FaUser, FaHeart, FaGlobe, FaLock, FaImage, FaEye } from "react-icons/fa";
import { Api } from "../../lib/api";

const MOVIE_GENRES = [
  "動作", "劇情", "科幻", "動畫", "喜劇", "驚悚",
  "恐怖", "愛情", "奇幻", "犯罪", "冒險", "紀錄片"
];

interface EnhancedProfileEditorProps {
  user: any;
  onUpdate: (updated: any) => void;
  onCancel?: () => void;
}

export function EnhancedProfileEditor({ user, onUpdate, onCancel }: EnhancedProfileEditorProps) {
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [favoriteGenres, setFavoriteGenres] = useState<string[]>([]);
  const [locale, setLocale] = useState("en");
  const [adultContent, setAdultContent] = useState(false);
  const [privacyLevel, setPrivacyLevel] = useState("public");
  
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user?.profile) {
      setDisplayName(user.profile.display_name || "");
      setBio(user.profile.bio || "");
      setAvatarUrl(user.profile.avatar_url || "");
      setFavoriteGenres(user.profile.favorite_genres || []);
      setLocale(user.profile.locale || "en");
      setAdultContent(user.profile.adult_content_opt_in || false);
      setPrivacyLevel(user.profile.privacy_level || "public");
    }
  }, [user]);

  const toggleGenre = (genre: string) => {
    setFavoriteGenres(prev =>
      prev.includes(genre)
        ? prev.filter(g => g !== genre)
        : [...prev, genre]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSaving(true);

    try {
      const updated = await Api.profile.updateMe({
        display_name: displayName,
        bio,
        avatar_url: avatarUrl,
        favorite_genres: favoriteGenres,
        locale,
        adult_content_opt_in: adultContent,
        privacy_level: privacyLevel,
      });
      
      setSuccess("個人資料已成功更新！");
      onUpdate(updated);
      window.dispatchEvent(new CustomEvent("profileUpdated"));
    } catch (err: any) {
      console.error("Failed to update profile:", err);
      const errorMsg = err?.message || err?.toString() || "儲存失敗，請再試一次。";
      setError(`儲存失敗: ${errorMsg}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Alerts */}
      {success && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg">
          {success}
        </div>
      )}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg">
          {error}
        </div>
      )}

      {/* 顯示名稱 */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
          <FaUser className="w-4 h-4 text-amber-400" />
          顯示名稱
        </label>
        <input
          type="text"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500/50 transition-all"
          placeholder="輸入你的暱稱"
        />
      </div>

      {/* 頭像 URL */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
          <FaImage className="w-4 h-4 text-amber-400" />
          頭像 URL
        </label>
        <input
          type="url"
          value={avatarUrl}
          onChange={(e) => setAvatarUrl(e.target.value)}
          className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500/50 transition-all"
          placeholder="data:image/jpeg;base64,... 或 https://..."
        />
        {avatarUrl && (
          <div className="mt-3">
            <img
              src={avatarUrl}
              alt="Preview"
              className="w-20 h-20 rounded-full object-cover border-2 border-slate-700"
            />
          </div>
        )}
      </div>

      {/* 個人簡介 */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
          <FaUser className="w-4 h-4 text-amber-400" />
          自我介紹 (bio)
        </label>
        <textarea
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          rows={4}
          className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500/50 transition-all resize-none"
          placeholder="大家好，我是愛運動的阿俊！！"
        />
        <p className="mt-2 text-xs text-slate-500">{bio.length} / 500 字元</p>
      </div>

      {/* 喜愛的類型 */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
          <FaHeart className="w-4 h-4 text-amber-400" />
          喜愛的類型（短號分類）
        </label>
        <div className="flex flex-wrap gap-2">
          {MOVIE_GENRES.map(genre => (
            <button
              key={genre}
              type="button"
              onClick={() => toggleGenre(genre)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                favoriteGenres.includes(genre)
                  ? "bg-amber-500 text-white shadow-lg shadow-amber-500/20"
                  : "bg-slate-700/50 text-slate-300 hover:bg-slate-600/50"
              }`}
            >
              {genre}
            </button>
          ))}
        </div>
      </div>

      {/* 語言 */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
          <FaGlobe className="w-4 h-4 text-amber-400" />
          語言 (locale)
        </label>
        <select
          value={locale}
          onChange={(e) => setLocale(e.target.value)}
          className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500/50 transition-all"
        >
          <option value="en">English</option>
          <option value="zh-TW">繁體中文</option>
          <option value="zh-CN">简体中文</option>
          <option value="ja">日本語</option>
          <option value="ko">한국어</option>
        </select>
      </div>

      {/* 成人內容偏好 */}
      <div className="flex items-center justify-between p-4 bg-slate-800/40 rounded-lg border border-slate-700/50">
        <div className="flex items-center gap-3">
          <FaEye className="w-5 h-5 text-amber-400" />
          <div>
            <p className="text-sm font-medium text-white">成人內容顯示</p>
            <p className="text-xs text-slate-400">允許顯示 18+ 內容</p>
          </div>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={adultContent}
            onChange={(e) => setAdultContent(e.target.checked)}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-amber-500/20 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500"></div>
        </label>
      </div>

      {/* 隱私設定 */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
          <FaLock className="w-4 h-4 text-amber-400" />
          隱私設定
        </label>
        <div className="grid grid-cols-3 gap-3">
          {["public", "friends", "private"].map(level => (
            <button
              key={level}
              type="button"
              onClick={() => setPrivacyLevel(level)}
              className={`p-4 rounded-lg text-sm font-medium transition-all ${
                privacyLevel === level
                  ? "bg-amber-500/20 text-amber-400 border-2 border-amber-500/50"
                  : "bg-slate-700/30 text-slate-400 border-2 border-slate-700/50 hover:border-slate-600/50"
              }`}
            >
              {level === "public" && "公開"}
              {level === "friends" && "僅好友"}
              {level === "private" && "私密"}
            </button>
          ))}
        </div>
      </div>

      {/* 儲存按鈕 */}
      <div className="pt-4 flex gap-4">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 px-6 py-4 bg-slate-700/50 hover:bg-slate-600/50 text-white font-medium rounded-xl border border-slate-600/50 hover:border-slate-500/50 transition-all duration-300"
          >
            取消
          </button>
        )}
        <button
          type="submit"
          disabled={saving}
          className={`${onCancel ? 'flex-1' : 'w-full'} px-6 py-4 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-bold rounded-xl transition-all duration-300 shadow-lg shadow-amber-500/30 hover:shadow-xl hover:shadow-amber-500/40 disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {saving ? "儲存中..." : "儲存變更"}
        </button>
      </div>
    </form>
  );
}
