# MovieIn 部署指南

##  部署檢查清單

### 階段 1: 後端部署 (Render.com)

#### 1.1 推送代碼到 GitHub
```powershell
git add .
git commit -m "chore: prepare for production deployment"
git push origin main
```

#### 1.2 在 Render 創建 Web Service
1. 前往 https://render.com 並登入
2. 點擊 **New  Web Service**
3. 連接你的 GitHub repository: **MovieIn_bmadProject**
4. 設定如下：
   - **Name**: moviein-api
   - **Region**: Singapore (或最接近用戶的區域)
   - **Branch**: main
   - **Root Directory**: backend
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt --no-cache-dir`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

#### 1.3 設定環境變數
在 Render 的 Environment 頁面，新增以下變數（從 backend/.env 複製值）：

```
DATABASE_URL=postgresql://...  (從 Neon 複製)
OPENAI_API_KEY=sk-...
TMDB_API_KEY=...
YOUTUBE_API_KEY=...
SENDGRID_API_KEY=...
MAIL_FROM_EMAIL=...
POSTER_BASE=https://image.tmdb.org/t/p/w500
CORS_ORIGINS=https://moviein.vercel.app,https://moviein-git-main-victorho1114.vercel.app
FRONTEND_URL=https://moviein.vercel.app
```

**重要**: 等前端部署完成後，回來更新 `CORS_ORIGINS` 和 `FRONTEND_URL`

#### 1.4 部署並驗證
- 等待部署完成（約 3-5 分鐘）
- 記下你的後端 URL（例如: `https://moviein-api.onrender.com`）
- 驗證端點：
  - https://moviein-api.onrender.com/db-test
  - https://moviein-api.onrender.com/docs

---

### 階段 2: 前端部署 (Vercel)

#### 2.1 更新前端環境變數
編輯 `frontend/.env.production`，將 API URL 替換為你的實際後端 URL：
```bash
NEXT_PUBLIC_API_BASE=https://moviein-api.onrender.com/api/v1
```

#### 2.2 部署到 Vercel

**選項 A: 使用 Vercel CLI（推薦）**
```powershell
cd frontend
npm install -g vercel  # 如果還沒安裝
vercel login
vercel --prod
```

**選項 B: 使用 Vercel 網頁界面**
1. 前往 https://vercel.com 並登入
2. 點擊 **Add New  Project**
3. Import 你的 GitHub repository
4. 設定如下：
   - **Framework Preset**: Next.js
   - **Root Directory**: frontend
   - **Build Command**: `npm run build` (自動檢測)
   - **Output Directory**: `.next` (自動檢測)

#### 2.3 設定環境變數
在 Vercel 的 Environment Variables 頁面，新增：
```
NEXT_PUBLIC_API_BASE=https://moviein-api.onrender.com/api/v1
NEXT_PUBLIC_USE_MOCKS=false
```

#### 2.4 部署並驗證
- 等待部署完成（約 1-2 分鐘）
- 記下你的前端 URL（例如: `https://moviein.vercel.app`）
- 測試功能是否正常

---

### 階段 3: 更新 CORS 設定

#### 3.1 回到 Render
使用前端的實際 URL 更新環境變數：
```
CORS_ORIGINS=https://moviein.vercel.app,https://moviein-git-main-victorho1114.vercel.app
FRONTEND_URL=https://moviein.vercel.app
```

#### 3.2 觸發重新部署
- 在 Render 點擊 **Manual Deploy  Deploy latest commit**
- 等待重新部署完成

---

##  部署後驗證清單

### 後端健康檢查
- [ ] `/db-test` 返回 " Connected to Neon"
- [ ] `/docs` 顯示 Swagger UI
- [ ] `/api/v1/home` 返回首頁數據
- [ ] `/api/recommend/v2` 推薦功能正常

### 前端功能驗證
- [ ] 首頁載入正常，無 CORS 錯誤
- [ ] 推薦系統可以正常輸入並獲得結果
- [ ] 電影圖片顯示正常
- [ ] 登入/註冊功能正常（如果已實作）

### 安全性檢查
- [ ] CORS 僅允許前端域名
- [ ] 環境變數未暴露在前端代碼
- [ ] HTTPS 連線正常

---

##  常見問題排解

### 問題 1: CORS 錯誤
**症狀**: 前端顯示 "Access to fetch has been blocked by CORS policy"

**解決方案**:
1. 檢查 Render 環境變數 `CORS_ORIGINS` 是否包含前端 URL
2. 確認前端 URL 沒有尾隨斜線
3. 觸發 Render 重新部署

### 問題 2: 後端 503 錯誤
**症狀**: 首次訪問後端 API 需要等待 30 秒

**原因**: Render 免費版會在閒置後休眠

**解決方案**:
- 升級到 Render Starter Plan (``/月) 獲得常駐服務
- 或接受首次訪問的等待時間

### 問題 3: 環境變數未生效
**症狀**: API 連線失敗或功能異常

**解決方案**:
1. 檢查 Vercel/Render 環境變數是否正確設定
2. 環境變數修改後需要重新部署
3. 確認 `.env.production` 不會被 Git 忽略（應該要提交）

### 問題 4: 資料庫連線失敗
**症狀**: `/db-test` 返回錯誤

**解決方案**:
1. 檢查 Neon 資料庫是否正常運行
2. 確認 `DATABASE_URL` 格式正確
3. 檢查 Neon 的 IP 白名單設定（如果有啟用）

---

##  成本估算

### 免費方案（適合初期）
- **Vercel**: ``/月
  - 100GB 流量
  - Unlimited 部署
  
- **Render**: ``/月
  - 750 小時/月
  -  閒置會休眠
  
- **Neon**: ``/月
  - 0.5GB 儲存
  - 足夠目前數據量

**總計**: ``/月

### 建議升級方案（如需不休眠後端）
- **Vercel**: ``/月（免費版足夠）
- **Render Starter**: ``/月（不休眠 + 更好效能）
- **Neon**: ``/月（免費版足夠）

**總計**: ``/月

---

##  部署後監控

### Vercel Analytics
- 在 Vercel 專案設定中啟用 Analytics
- 查看頁面訪問量、載入時間

### Render Logs
- 在 Render Dashboard 查看即時日誌
- 監控 API 請求和錯誤

### 效能監控建議
```python
# 未來可加入 backend/app/main.py
from fastapi import Request
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"{request.method} {request.url.path} - {process_time:.2f}s")
    return response
```

---

##  後續優化計劃

### 第 1 週：收集數據
- 啟用 Analytics
- 觀察用戶行為
- 記錄推薦品質反饋

### 第 2-3 週：推薦系統優化
- 根據真實數據調整映射表
- 實作三層漸進式匹配
- A/B 測試不同算法

### 第 4 週：功能完善
- 優化 UI/UX
- 加入用戶反饋機制
- 效能優化

---

##  部署完成後的下一步

1. **推送 Git 更新**
   ```bash
   git add DEPLOYMENT.md backend/render.yaml frontend/.env.production backend/app/main.py
   git commit -m "docs: add deployment guide and production configs"
   git push origin main
   ```

2. **開始部署**
   - 按照上述步驟執行後端部署
   - 接著執行前端部署
   - 最後更新 CORS 設定

3. **驗證並分享**
   - 完成所有驗證檢查
   - 分享你的 MovieIn 網站！

---

**需要協助？** 隨時回來找 Winston（架構師）討論！
