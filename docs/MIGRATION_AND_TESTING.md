# Migration & Testing — MovieIn

這份簡短說明幫你在本機或在 Neon 上套用剛建立的 Alembic migration，並提供一些測試指令（PowerShell）來驗證朋友系統的變更（soft-delete、undo、cancel sent request）。

> 假設你在 `backend` 目錄下有 `alembic.ini` 與 `backend/db/versions/`，且 `backend/db/database.py` 會從 `DATABASE_URL` 讀取連線字串。

準備

1. 建議先在 Neon 建立一個 Branch（或在 staging DB 測試），避免直接對 production DB 做變更。
2. 本地建立並啟動 Python virtualenv：

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

設定 DATABASE_URL

在 PowerShell 中：

```powershell
$env:DATABASE_URL = "postgresql://<user>:<pass>@<host>:5432/<db_name>"
```

替換為你的 Neon connection string（含使用者與密碼）。

套用 migration

```powershell
cd backend
alembic upgrade head
```

驗證資料表/欄位

使用 `psql` 或 Neon UI 檢查 `friendships` 是否有 `deleted_at` 欄位：

```powershell
# 若 psql 可用
psql $env:DATABASE_URL -c "\d+ friendships"
```

或使用簡單的 SQL 檢查是否有值：

```powershell
psql $env:DATABASE_URL -c "SELECT column_name FROM information_schema.columns WHERE table_name='friendships';"
```

啟動後端與前端

```powershell
# 後端 (在 backend)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 前端 (在 frontend)
cd ../frontend
pnpm install   # 或 npm install / yarn
pnpm dev
```

快速用 PowerShell 驗證 API

先把 token 放到環境變數（或直接在 headers 使用）：

```powershell
$token = "<YOUR_TOKEN>"
$headers = @{ Authorization = "Bearer $token" }

# 1) 取得 pending count
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/v1/friends/requests/count" -Headers $headers

# 2) 取消已發出的邀請（假設有 friendship id）
Invoke-RestMethod -Method Delete -Uri "http://127.0.0.1:8000/api/v1/friends/requests/<FRIENDSHIP_ID>" -Headers $headers

# 3) 軟刪好友（移除）
Invoke-RestMethod -Method Delete -Uri "http://127.0.0.1:8000/api/v1/friends/<FRIEND_ID>" -Headers $headers

# 4) 復原
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/friends/<FRIEND_ID>/restore" -Headers $headers
```

注意事項

- 背景清除機制：目前在 `app.main` 的 startup event 中會啟動一個簡單的 asyncio loop，每分鐘檢查一次 `friendships` 中 `status='deleted'` 且 `deleted_at` 超過 5 分鐘的紀錄並永久刪除。若你偏好使用資料庫自己的排程工具（pg_cron）或外部 worker（Celery / APScheduler），請告訴我，我可以協助改成更健壯的方案。

- 若你的部署環境在 serverless 或不允許長時間 background task，請不要依賴 `startup` loop；改用 DB-side 或外部定時器會比較穩妥。

需要我幫忙的事

- 我可以產生一個更完整的 migration release note，或把 background purge 改為移到 `friendship_history` 表（保留紀錄而非刪除）。
- 我也可以幫你在 CI 中加入一個 `alembic upgrade` 的 job（在 staging branch 測試再上 production）。

如果要我把 README 放到其他位置（例如 `backend/README.md` 或 `docs/`），告訴我你偏好的路徑，我會移動它。
