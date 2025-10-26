import { getHomeFeed } from "./services";

export async function HomeFeed() {
  const data = await getHomeFeed();

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-bold">Home</h1>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {data.trending.map((m) => (
          <article key={m.id} className="border rounded p-3">
            <div className="text-sm opacity-70">{m.year}</div>
            <div className="font-semibold">{m.title}</div>
            <div className="text-xs opacity-70">⭐ {m.rating}</div>
          </article>
        ))}
      </div>
    </section>
  );
}
