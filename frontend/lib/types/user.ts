
// 這個 interface 必須 "完全對齊" 
// 你在 backend/app/schemas/user.py 中定義的 ProfileBase
export interface Profile {
  display_name: string | null;
  avatar_url: string | null;
  // locale: string | null; // (未來可以擴充)
  // adult_content_opt_in: boolean; // (未來可以擴充)
}

// 這個 interface 必須 "完全對齊" 
// 你在 backend/app/schemas/user.py 中定義的 UserPublic
export interface UserPublic {
  user_id: string;
  email: string;
  // provider: string; // (我們在 auth.py 忘了加，但稍後可以補上)
  profile: Profile | null;
}

// 對齊 schemas.Token
export interface AuthToken {
  access_token: string;
  token_type: string;
}

// 對齊 schemas.UserCreate
export type UserCreate = {
  email: string;
  password: string;
  display_name?: string;
};

// 對齊 schemas.UserLogin
export type UserLogin = {
  email: string;
  password: string;
};

// [新增！] 對應 schemas.ProfileUpdate
export type ProfileUpdate = {
  display_name?: string | null;
  avatar_url?: string | null;
};

// [新增！] 對應 schemas.PasswordChange
export type PasswordChange = {
  old_password: string;
  new_password: string;
};

// frontend/lib/types/user.ts (在最底部新增)
export type ForgotPasswordRequest = {
  email: string;
};

// [新增！] 對應後端的 ResetPasswordRequest
export type ResetPasswordPayload = {
  token: string;
  new_password: string;
};