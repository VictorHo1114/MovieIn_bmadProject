// app/search/page.tsx
import { searchMovies } from "@/features/search/services";
export default async function Page({ searchParams }: { searchParams: { q?: string } }) {
  const q = searchParams.q ?? "";
  const data = q ? await searchMovies(q) : { items: [] };
  return <pre>{JSON.stringify(data, null, 2)}</pre>;
}