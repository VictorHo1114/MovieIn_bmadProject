/**
 * 集中管理 Watchlist 和 Top10 狀態
 * 避免每個 MovieCard 都發送重複的 API 請求
 */

import { Api } from './api';

interface MovieListState {
  watchlistIds: Set<number>;
  top10Ids: Set<number>;
  isLoading: boolean;
  lastFetchTime: number;
  listeners: Set<() => void>;
}

const CACHE_DURATION = 5000; // 5 秒快取

class MovieListStore {
  private state: MovieListState = {
    watchlistIds: new Set(),
    top10Ids: new Set(),
    isLoading: false,
    lastFetchTime: 0,
    listeners: new Set(),
  };

  private fetchPromise: Promise<void> | null = null;

  /**
   * 訂閱狀態變化
   */
  subscribe(listener: () => void) {
    this.state.listeners.add(listener);
    return () => {
      this.state.listeners.delete(listener);
    };
  }

  /**
   * 通知所有訂閱者
   */
  private notify() {
    this.state.listeners.forEach(listener => listener());
  }

  /**
   * 檢查快取是否有效
   */
  private isCacheValid(): boolean {
    const now = Date.now();
    return (now - this.state.lastFetchTime) < CACHE_DURATION;
  }

  /**
   * 獲取列表資料（帶快取）
   */
  async fetch(force: boolean = false): Promise<void> {
    // 如果快取有效且不強制刷新，直接返回
    if (!force && this.isCacheValid()) {
      console.log('📦 使用快取的列表資料');
      return;
    }

    // 如果正在請求中，返回現有的 Promise
    if (this.fetchPromise) {
      console.log('⏳ 等待現有請求完成...');
      return this.fetchPromise;
    }

    // 開始新的請求
    console.log('🔄 刷新列表資料...');
    this.state.isLoading = true;
    this.notify();

    this.fetchPromise = (async () => {
      try {
        const token = localStorage.getItem('authToken');
        if (!token) {
          this.state.watchlistIds.clear();
          this.state.top10Ids.clear();
          this.state.lastFetchTime = Date.now();
          return;
        }

        // 並行請求
        const [watchlistData, top10Data] = await Promise.all([
          Api.watchlist.getAll().catch(() => ({ items: [], total: 0 })),
          Api.top10.getAll().catch(() => ({ items: [], total: 0 })),
        ]);

        // 更新狀態
        this.state.watchlistIds = new Set(watchlistData.items.map(item => item.tmdb_id));
        this.state.top10Ids = new Set(top10Data.items.map(item => item.tmdb_id));
        this.state.lastFetchTime = Date.now();

        console.log(`✅ 列表已更新: Watchlist=${this.state.watchlistIds.size}, Top10=${this.state.top10Ids.size}`);
      } catch (error) {
        console.error('❌ 獲取列表失敗:', error);
      } finally {
        this.state.isLoading = false;
        this.fetchPromise = null;
        this.notify();
      }
    })();

    return this.fetchPromise;
  }

  /**
   * 檢查電影是否在 Watchlist 中
   */
  isInWatchlist(tmdbId: number): boolean {
    return this.state.watchlistIds.has(tmdbId);
  }

  /**
   * 檢查電影是否在 Top10 中
   */
  isInTop10(tmdbId: number): boolean {
    return this.state.top10Ids.has(tmdbId);
  }

  /**
   * 添加到 Watchlist（本地更新）
   */
  addToWatchlist(tmdbId: number) {
    this.state.watchlistIds.add(tmdbId);
    this.notify();
  }

  /**
   * 從 Watchlist 移除（本地更新）
   */
  removeFromWatchlist(tmdbId: number) {
    this.state.watchlistIds.delete(tmdbId);
    this.notify();
  }

  /**
   * 添加到 Top10（本地更新）
   */
  addToTop10(tmdbId: number) {
    this.state.top10Ids.add(tmdbId);
    this.notify();
  }

  /**
   * 從 Top10 移除（本地更新）
   */
  removeFromTop10(tmdbId: number) {
    this.state.top10Ids.delete(tmdbId);
    this.notify();
  }

  /**
   * 獲取 Top10 數量
   */
  getTop10Count(): number {
    return this.state.top10Ids.size;
  }

  /**
   * 清空快取（登出時使用）
   */
  clear() {
    this.state.watchlistIds.clear();
    this.state.top10Ids.clear();
    this.state.lastFetchTime = 0;
    this.notify();
  }
}

// 單例模式
export const movieListStore = new MovieListStore();
