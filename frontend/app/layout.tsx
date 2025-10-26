import './globals.css';
import NavBar from '@/components/NavBar';

export const metadata = { title: 'MovieIN', description: 'Movie recommendation MVP' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-neutral-950 text-neutral-100">
        <NavBar />
        <main className="mx-auto max-w-6xl p-4">{children}</main>
      </body>
    </html>
  );
}
