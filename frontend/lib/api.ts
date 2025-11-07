// 1. [修改！] 我們一次性導入所有需要的 http 函式
import { getJSON, postJSON, patchJSON } from "./http";

// 2. 導入你舊的型別 (保持不變)
import type { HomeFeed, SearchResult } from "./types";

// 3. [修改！] 導入「所有」需要的 User 型別
import type {
  UserPublic,
  AuthToken,
  UserCreate,
  UserLogin,
  ProfileUpdate,
  PasswordChange, // <-- [新增！] 導入 PasswordChange
  ForgotPasswordRequest, // <-- [新增！] (請確保已在 user.ts 中定義)
  ResetPasswordPayload
} from "./types/user";

export const Api = {
  // --- 你現有的 Home (保持不變) ---
  home: () => getJSON<HomeFeed>("/home"),

  // --- 你現有的 Search (保持不變) ---
  search: (q: string) =>
    getJSON<SearchResult>(`/search?q=${encodeURIComponent(q)}`),

  // --- (重要！) 修改 Profile ---
  profile: {
    me: () => getJSON<UserPublic>("/auth/me"),
    
    // [新增！] (需求 2) 更新 Profile (名稱) 的 API
    updateMe: (data: ProfileUpdate): Promise<UserPublic> => {
      // 這會呼叫 /api/v1/profile/me
      return patchJSON<UserPublic>("/profile/me", data);
    }
  },

  // --- (重要！) 修改 Auth ---
  auth: {
    signup: (data: UserCreate): Promise<UserPublic> => {
      return postJSON<UserPublic>("/auth/signup", data);
    },

    login: (data: UserLogin): Promise<AuthToken> => {
      return postJSON<AuthToken>("/auth/login", data);
    },
    
    // [新增！] (需求 2) 更改密碼的 API
    changePassword: (data: PasswordChange): Promise<UserPublic> => {
      // 這會呼叫 /api/v1/auth/change-password
      return postJSON<UserPublic>("/auth/change-password", data);
    },


    forgotPassword: (data: ForgotPasswordRequest): Promise<{ message: string }> => {
      return postJSON<{ message: string }>("/auth/forgot-password", data);
    },

    resetPassword: (data: ResetPasswordPayload): Promise<UserPublic> => {
      return postJSON<UserPublic>("/auth/reset-password", data);
    }
  },
};