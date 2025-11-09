================================================================================
 混合推薦系統 - 快速開始指南
================================================================================

##  P1 完成狀態

【已完成】
 P0 測試（100% 通過）
 API 路由整合
 邏輯測試（100% 通過）
 向後兼容性保證
 A/B 測試支援

【待完成】
 啟動後端伺服器
 HTTP 實際測試
 前端整合

================================================================================
 下一步操作清單
================================================================================

### 1. 啟動後端伺服器（立即執行）

```powershell
# 在 backend 目錄
cd C:\Users\User\Desktop\bmad-method\backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 測試 API 端點

#### 測試 1: 系統資訊
```powershell
curl http://localhost:8000/api/recommend/v2/system-info
```

#### 測試 2: 抽象查詢（預期 Embedding）
```powershell
curl -X POST http://localhost:8000/api/recommend/v2/movies `
  -H "Content-Type: application/json" `
  -d '{\"query\": \"溫暖治癒的超級英雄電影\", \"selected_moods\": [], \"selected_genres\": []}'
```

#### 測試 3: 明確查詢 + Buttons（預期 Feature）
```powershell
curl -X POST http://localhost:8000/api/recommend/v2/movies `
  -H "Content-Type: application/json" `
  -d '{\"query\": \"超級英雄動作片\", \"selected_moods\": [\"動作冒險\", \"視覺饗宴\"], \"selected_genres\": [\"Action\"]}'
```

#### 測試 4: 純 Buttons（預期 Feature）
```powershell
curl -X POST http://localhost:8000/api/recommend/v2/movies `
  -H "Content-Type: application/json" `
  -d '{\"query\": \"\", \"selected_moods\": [\"動作冒險\"], \"selected_genres\": [\"Science Fiction\", \"Action\"]}'
```

#### 測試 5: 舊版推薦（對照組）
```powershell
curl -X POST http://localhost:8000/api/recommend/v2/movies `
  -H "Content-Type: application/json" `
  -d '{\"query\": \"溫暖治癒的電影\", \"use_legacy\": true}'
```

### 3. 前端整合（待執行）

#### 修改 HomeClient.tsx

```typescript
// 更新 API 調用
const response = await fetch('/api/recommend/v2/movies', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: userInput,
    selected_moods: selectedMoodLabels,    // 傳遞 mood buttons
    selected_genres: selectedGenreLabels,  // 傳遞 genre buttons
    randomness: 0.3,                       // 可選
    decision_threshold: 40                 // 可選
  })
});

const data = await response.json();
console.log('Strategy:', data.strategy);  // "Feature" or "Embedding"
console.log('Movies:', data.movies);
```

#### 可選：顯示策略指示器

```tsx
{data.strategy === 'Embedding' && (
  <div className="strategy-badge"> 語義匹配</div>
)}
{data.strategy === 'Feature' && (
  <div className="strategy-badge"> 特徵匹配</div>
)}
```

================================================================================
 測試檢查清單
================================================================================

- [ ] 後端伺服器啟動成功
- [ ] /api/recommend/v2/system-info 返回正確資訊
- [ ] 抽象查詢觸發 Embedding 路徑
- [ ] Buttons 查詢觸發 Feature 路徑
- [ ] 純 Buttons 觸發 Feature 路徑
- [ ] use_legacy=true 使用舊版推薦
- [ ] 前端可以正確調用新 API
- [ ] 前端可以顯示推薦結果
- [ ] 前端可以傳遞 mood/genre buttons

================================================================================
 監控指標
================================================================================

### 需要追蹤的數據

1. **路徑使用比例**
   - Feature 使用次數
   - Embedding 使用次數
   - Feature/Embedding 比例

2. **效能指標**
   - 平均響應時間
   - Feature 路徑平均時間
   - Embedding 路徑平均時間

3. **成本指標**
   - OpenAI API 調用次數
   - 每日 API 成本
   - 每次推薦平均成本

4. **品質指標**
   - 用戶點擊率
   - 用戶滿意度
   - 推薦準確度

================================================================================
 故障排除
================================================================================

### 問題 1: 伺服器啟動失敗
解決: 檢查虛擬環境是否啟動，檢查 port 8000 是否被佔用

### 問題 2: API 返回 500 錯誤
解決: 檢查終端日誌，確認資料庫連接正常

### 問題 3: Embedding 總是失敗
解決: 檢查 OPENAI_API_KEY 環境變數，檢查 API 配額

### 問題 4: 前端無法連接後端
解決: 檢查 CORS 設定，確認前端 proxy 配置正確

================================================================================
 支援資源
================================================================================

- 報告文件: P0_TEST_SUCCESS_REPORT.md
- 整合報告: P1_API_INTEGRATION_REPORT.md
- 路由檔案: app/routers/simple_recommend_router.py
- 推薦邏輯: app/services/simple_recommend.py
- 測試腳本: test_api_route.py

================================================================================
 成功標準
================================================================================

 後端伺服器正常運行
 所有 API 端點回應正確
 Feature/Embedding 路徑正確切換
 前端成功整合並顯示結果
 系統穩定運行無錯誤

當所有標準達成，P1 任務即完成！

================================================================================
