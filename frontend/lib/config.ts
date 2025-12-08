// API 基底位址 & 是否啟用 mock
// 預設使用生產環境 API，本地開發可通過環境變數覆蓋
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? 'https://moviein-api.onrender.com/api/v1'; 

export const USE_MOCKS =
  (process.env.NEXT_PUBLIC_USE_MOCKS ?? "false").toLowerCase() === "true";
