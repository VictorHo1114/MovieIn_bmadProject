// frontend/app/(app)/home/page.tsx

// [修正！] 跳三層 (../../../)
// 邏輯：home/ ➡️ (app)/ ➡️ app/ ➡️ frontend/ ➡️ features/home
import { HomeFeed } from '../../../features/home';

export default function HomePage() {
  // 頁面 (Page) 的職責很簡單：
  // 只負責「組裝」功能 (Features)
  return <HomeFeed />;
}