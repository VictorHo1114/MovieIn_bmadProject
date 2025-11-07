// 1. 導入我們新建立的 ProfileFeed 元件
// (路徑: .../app/(app)/profile -> ../../ -> app/ -> ../ -> frontend/ -> features/profile)
import { ProfileFeed } from '../../../features/profile';

export default function ProfilePage() {
  
  // 頁面 (Page) 的職責很簡單：
  // 只負責「組裝」功能 (Features)
  return <ProfileFeed />;
}