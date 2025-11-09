# 推薦系統診斷報告

## 當前架構分析

### 三層協作機制：
1. **Rule-Based（規則層）**
   - Regex 關鍵字匹配
   - Feature label 映射
   - 語言/類型硬規則

2. **GPT-4（語意層）**
   - 自然語言理解
   - 年份推導
   - 情緒解析

3. **Embedding（語義層）**
   - Vector similarity search
   - 候選電影重排序
   - Top 10 精選

## 問題診斷

### 問題 1：找不到 007
**根本原因：**
- GPT 解析「007」 沒有映射到具體 keywords
- Rule-based 沒有「007」的 regex 規則
- Embedding 需要依賴前兩層提供候選電影

**當前流程：**
用戶輸入「007」 GPT 解析  Rule補充  TMDB API（genres/year）  Embedding重排序

**問題所在：**
TMDB API 查詢沒有包含「007」或「James Bond」關鍵字！

### 問題 2：相同輸入 = 相同結果
**根本原因：**
- Embedding 是確定性算法（cosine similarity）
- 沒有隨機性或多樣性機制
- 沒有用戶歷史或上下文

### 問題 3：MovieCard 渲染動畫
需要前端實作漸入動畫。

