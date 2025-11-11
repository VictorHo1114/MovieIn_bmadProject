// 1. [修改！] 我們一次性導入所有需要的 http 函式
import { getJSON, postJSON, patchJSON, deleteJSON, putJSON } from "./http";

// 2. 導入你舊的型別 (保持不變)
import type { HomeFeed, SearchResult } from "./types";

// 3. [修改！] 導入「所有」需要的 User 型別
import type {
  UserPublic,
  AuthToken,
  UserCreate,
  UserLogin,
  ProfileUpdate,
  PasswordChange,
  ForgotPasswordRequest,
  ResetPasswordPayload
} from "./types/user";

// 4. [新增！] 導入 Movie, Watchlist, Top10 型別
export interface FrontendMovie {
  id: number;
  title: string;
  overview: string;
  poster_url: string | null;
  release_year: number | null;
  vote_average: number;
}

export interface WatchlistItem {
  id: string;
  user_id: string;
  tmdb_id: number;
  added_at: string;
  notes: string | null;
  is_watched: boolean;
  priority: number;
  movie: FrontendMovie;
}

export interface Top10Item {
  id: string;
  user_id: string;
  tmdb_id: number;
  rank: number;
  added_at: string;
  notes: string | null;
  rating_by_user: number | null;
  category: string | null;
  movie: FrontendMovie;
}

export const Api = {
  // --- 你現有的 Home (保持不變) ---
  home: () => getJSON<HomeFeed>("/home"),

  // --- 你現有的 Search (保持不變) ---
  search: (q: string) =>
    getJSON<SearchResult>(`/search?q=${encodeURIComponent(q)}`),
  getRecommendations: (params: {
    query: string;
    genres: string[];
    moods: string[];
    eras: string[];
  }) => getJSON<{ movies: any[]; strategy: string }>("/recommendations", {
    method: "POST",
    body: JSON.stringify(params),
  }),

  // --- [新增！] Movies API (使用絕對路徑繞過 /api/v1 base) ---
  movies: {
    getPopular: (page: number = 1, limit: number = 20) => 
      getJSON<FrontendMovie[]>(`http://127.0.0.1:8000/api/movies/popular?page=${page}&limit=${limit}`),
    
    getRandom: (limit: number = 20) => 
      getJSON<FrontendMovie[]>(`http://127.0.0.1:8000/api/movies/random/recommendations?limit=${limit}`),
    
    getById: (tmdbId: number) => 
      getJSON<FrontendMovie>(`http://127.0.0.1:8000/api/movies/${tmdbId}`),
    
    checkExists: (tmdbId: number) => 
      getJSON<{ exists: boolean; tmdb_id: number }>(`http://127.0.0.1:8000/api/movies/check/${tmdbId}`),
  },

  // --- [新增！] Watchlist API (使用絕對路徑繞過 /api/v1 base) ---
  watchlist: {
    getAll: () => 
      getJSON<{ items: WatchlistItem[]; total: number }>("http://127.0.0.1:8000/api/watchlist"),
    
    add: (tmdbId: number, data?: { notes?: string; priority?: number }) => 
      postJSON<WatchlistItem>(`http://127.0.0.1:8000/api/watchlist/${tmdbId}`, data || {}),
    
    remove: (tmdbId: number) => 
      deleteJSON(`http://127.0.0.1:8000/api/watchlist/${tmdbId}`),
    
    update: (tmdbId: number, data: { notes?: string; is_watched?: boolean; priority?: number }) => 
      patchJSON<WatchlistItem>(`http://127.0.0.1:8000/api/watchlist/${tmdbId}`, data),
  },

  // --- [新增！] Top10 API (使用絕對路徑繞過 /api/v1 base) ---
  top10: {
    getAll: (category?: string) => {
      const url = category 
        ? `http://127.0.0.1:8000/api/top10?category=${encodeURIComponent(category)}`
        : "http://127.0.0.1:8000/api/top10";
      return getJSON<{ items: Top10Item[]; total: number }>(url);
    },
    
    add: (tmdbId: number, data?: { notes?: string; rating_by_user?: number; category?: string; rank?: number }) => 
      postJSON<Top10Item>(`http://127.0.0.1:8000/api/top10/${tmdbId}`, data || {}),
    
    remove: (tmdbId: number, category?: string) => {
      const url = category 
        ? `http://127.0.0.1:8000/api/top10/${tmdbId}?category=${encodeURIComponent(category)}`
        : `http://127.0.0.1:8000/api/top10/${tmdbId}`;
      return deleteJSON(url);
    },
    
    update: (tmdbId: number, data: { notes?: string; rating_by_user?: number; category?: string; rank?: number }, category?: string) => {
      const url = category 
        ? `http://127.0.0.1:8000/api/top10/${tmdbId}?category=${encodeURIComponent(category)}`
        : `http://127.0.0.1:8000/api/top10/${tmdbId}`;
      return patchJSON<Top10Item>(url, data);
    },
    
    reorder: (items: Array<{ id: string; rank: number }>) => 
      putJSON<{ items: Top10Item[]; total: number }>("http://127.0.0.1:8000/api/top10/reorder", { items }),
  },

  // --- (重要！) 修改 Profile ---
  profile: {
    me: () => getJSON<UserPublic>("/auth/me"),
    
    updateMe: (data: ProfileUpdate): Promise<UserPublic> => {
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
    
    changePassword: (data: PasswordChange): Promise<UserPublic> => {
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