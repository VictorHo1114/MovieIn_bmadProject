// 1. [修改！] ?�們�?次性�??��??��?要�? http ?��?
import { getJSON, postJSON, patchJSON, deleteJSON, putJSON } from "./http";

// 2. 導入你�??��???(保�?不�?)
import type { HomeFeed, SearchResult } from "./types";

// 3. [修改！] 導入?��??�」�?要�? User ?�別
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

// 4. [?��?！] 導入 Movie, Watchlist, Top10 ?�別
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

// Quiz Types
export interface MovieReference {
  title: string;
  year: number;
  poster_url: string | null;
}

export interface DailyQuiz {
  id: number;
  date: string;
  question: string;
  options: string[];
  difficulty: 'easy' | 'medium' | 'hard';
  category: string | null;
  movie_reference: MovieReference | null;
  correct_answer?: number; // Optional: shown after answering
  explanation?: string | null; // Optional: shown after answering
}

export interface QuizAttempt {
  id: number;
  quiz_id: number;
  user_answer: number | null;
  is_correct: boolean;
  points_earned: number;
  time_spent: number;
  answered_at: string;
}

export interface TodayQuizResponse {
  quiz: DailyQuiz | null;
  user_attempt: QuizAttempt | null;
  has_answered: boolean;
  time_until_next: string | null;
  daily_attempts: number;
  daily_limit: number;
  remaining_attempts: number;
}

export interface UserStats {
  total_points: number;
  previous_points: number;
  level: number;
  previous_level: number;
  level_up: boolean;
  global_rank: number | null;
  friend_rank: number | null;
}

export interface QuizSubmitResponse {
  is_correct: boolean;
  correct_answer: number;
  points_earned: number;
  explanation: string | null;
  user_stats: UserStats;
  movie_reference: MovieReference | null;
}

export interface AllTodayQuizzesResponse {
  quizzes: DailyQuiz[];
  user_attempts: QuizAttempt[];
  daily_attempts: number;
  daily_limit: number;
  is_first_round: boolean;
  time_until_next: string | null;
}

export const Api = {
  // --- 你現?��? Home (保�?不�?) ---
  home: () => getJSON<HomeFeed>("/home"),

  // --- 你現?��? Search (保�?不�?) ---
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

  // --- [?��?！] Movies API (使用絕�?路�?繞�? /api/v1 base) ---
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

  // --- [?��?！] Watchlist API (使用絕�?路�?繞�? /api/v1 base) ---
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

  // --- [?��?！] Top10 API (使用絕�?路�?繞�? /api/v1 base) ---
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

  // --- (?��?�? 修改 Profile ---
  profile: {
    me: () => getJSON<UserPublic>("/auth/me"),
    
    updateMe: (data: ProfileUpdate): Promise<UserPublic> => {
      return patchJSON<UserPublic>("/profile/me", data);
    }
    ,
    getById: (userId: string) => getJSON<UserPublic>(`/profile/${userId}`),
  },

  // --- (?��?�? 修改 Auth ---
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

  // --- Quiz API ---
  quiz: {
    getToday: () =>
      getJSON<TodayQuizResponse>("http://127.0.0.1:8000/api/v1/quiz/today"),
    
    getAllToday: () =>
      getJSON<AllTodayQuizzesResponse>("http://127.0.0.1:8000/api/v1/quiz/today/all"),
    
    submit: (data: { quiz_id: number; answer: number | null; time_spent: number; practice_mode?: boolean }) =>
      postJSON<QuizSubmitResponse>("http://127.0.0.1:8000/api/v1/quiz/submit", data),
  },
};
