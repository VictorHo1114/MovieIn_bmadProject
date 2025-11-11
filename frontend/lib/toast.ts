/**
 * 簡單的 Toast 通知系統
 * 用於替代 alert() 提供更好的用戶體驗
 */

type ToastType = 'success' | 'error' | 'info' | 'warning';

interface ToastOptions {
  message: string;
  type?: ToastType;
  duration?: number;
}

export function showToast({ message, type = 'info', duration = 3000 }: ToastOptions) {
  // 檢查是否在瀏覽器環境
  if (typeof window === 'undefined') return;

  // 創建 toast 元素
  const toast = document.createElement('div');
  // 固定在左上方，使用 inline style 控制動畫
  toast.className = `fixed top-20 left-4 z-50 px-6 py-3 rounded-lg shadow-lg transition-all duration-300`;
  
  // 根據類型設置顏色
  const colors = {
    success: 'bg-green-500 text-white',
    error: 'bg-red-500 text-white',
    info: 'bg-blue-500 text-white',
    warning: 'bg-yellow-500 text-gray-900',
  };
  
  toast.className += ` ${colors[type]}`;
  toast.textContent = message;
  
  // 初始狀態：隱藏在左邊外側
  toast.style.transform = 'translateX(-120%)';
  toast.style.opacity = '0';
  
  // 添加到 DOM
  document.body.appendChild(toast);
  
  // 動畫進入（滑入到正常位置）
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      toast.style.transform = 'translateX(0)';
      toast.style.opacity = '1';
    });
  });
  
  // 自動移除（滑回左邊）
  setTimeout(() => {
    toast.style.transform = 'translateX(-120%)';
    toast.style.opacity = '0';
    setTimeout(() => {
      if (document.body.contains(toast)) {
        document.body.removeChild(toast);
      }
    }, 300);
  }, duration);
}

// 便捷方法
export const toast = {
  success: (message: string, duration?: number) => 
    showToast({ message, type: 'success', duration }),
  error: (message: string, duration?: number) => 
    showToast({ message, type: 'error', duration }),
  info: (message: string, duration?: number) => 
    showToast({ message, type: 'info', duration }),
  warning: (message: string, duration?: number) => 
    showToast({ message, type: 'warning', duration }),
};
