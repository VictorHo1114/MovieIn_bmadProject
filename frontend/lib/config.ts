// API 基底位址 & 是否啟用 mock
// 生產環境自動使用 Render API，開發環境使用本地
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? 
  (process.env.NODE_ENV === 'production' 
    ? 'https://moviein-api.onrender.com/api/v1'
    : 'http://127.0.0.1:8000/api/v1'); 

export const USE_MOCKS =
  (process.env.NEXT_PUBLIC_USE_MOCKS ?? "false").toLowerCase() === "true";
