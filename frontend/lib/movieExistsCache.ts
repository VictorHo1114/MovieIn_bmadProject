/**
 * 電影存在性快取
 * 用於批量檢查電影是否在資料庫中，避免每個 MovieCard 都單獨調用 API
 */

import { Api } from './api';

interface ExistsCacheState {
  // tmdbId -> exists
  cache: Map<number, boolean>;
  // 正在檢查中的 Promise，避免重複請求
  pendingChecks: Map<number, Promise<boolean>>;
}

class MovieExistsCache {
  private state: ExistsCacheState = {
    cache: new Map(),
    pendingChecks: new Map(),
  };

  /**
   * 檢查單個電影是否存在（帶快取）
   */
  async checkExists(tmdbId: number): Promise<boolean> {
    // 1. 檢查快取
    if (this.state.cache.has(tmdbId)) {
      return this.state.cache.get(tmdbId)!;
    }

    // 2. 檢查是否正在請求中（避免重複）
    if (this.state.pendingChecks.has(tmdbId)) {
      return this.state.pendingChecks.get(tmdbId)!;
    }

    // 3. 發起新請求
    const promise = this._doCheck(tmdbId);
    this.state.pendingChecks.set(tmdbId, promise);

    try {
      const exists = await promise;
      this.state.cache.set(tmdbId, exists);
      return exists;
    } finally {
      this.state.pendingChecks.delete(tmdbId);
    }
  }

  /**
   * 實際執行檢查
   */
  private async _doCheck(tmdbId: number): Promise<boolean> {
    try {
      const result = await Api.movies.checkExists(tmdbId);
      return result.exists;
    } catch (error) {
      console.error(`檢查電影 ${tmdbId} 是否存在失敗:`, error);
      // 錯誤時預設為存在（較安全）
      return true;
    }
  }

  /**
   * 批量檢查多個電影（優化版）
   * 注意：目前後端沒有批量端點，所以這裡使用 Promise.all 並行請求
   */
  async checkBatch(tmdbIds: number[]): Promise<Map<number, boolean>> {
    const results = new Map<number, boolean>();
    
    // 使用 Promise.all 並行檢查所有電影
    await Promise.all(
      tmdbIds.map(async (id) => {
        const exists = await this.checkExists(id);
        results.set(id, exists);
      })
    );

    return results;
  }

  /**
   * 預設某些電影存在（用於從 DB 載入的電影）
   */
  markAsExists(tmdbIds: number[]) {
    tmdbIds.forEach(id => {
      this.state.cache.set(id, true);
    });
  }

  /**
   * 清空快取
   */
  clear() {
    this.state.cache.clear();
    this.state.pendingChecks.clear();
  }

  /**
   * 獲取快取大小（除錯用）
   */
  getCacheSize(): number {
    return this.state.cache.size;
  }
}

// 單例
export const movieExistsCache = new MovieExistsCache();
