// app/search/page.tsx
import SearchForm from "@/features/search/SearchForm";

export default function Page() {
  return (
    <div className="py-6">
      <h1 className="text-2xl font-bold mb-3">Search</h1>
      <SearchForm />
      <div className="text-sm opacity-70 mt-3">Use the form above to search movies (results shown below the form).</div>
    </div>
  )
}