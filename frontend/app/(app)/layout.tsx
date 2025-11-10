// 檔案：frontend/app/(app)/layout.tsx (這是新檔案)

// 假設你的 NavBar 元件路徑是 '@/components/NavBar'
// (請依你的實際路徑修改)
import { NavBar } from '../../components/NavBar';

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div>
      {/* NavBar 只會出現在 (app) 群組中的頁面 */}
      <NavBar />
      <main>
        {children}
      </main>
    </div>
  );
}