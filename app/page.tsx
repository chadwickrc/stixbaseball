import Link from "next/link";
import { supabase, type School } from "@/lib/supabase";

export const revalidate = 60;

export default async function HomePage() {
  const { data: schools, error } = await supabase
    .from("schools")
    .select("*")
    .order("name");

  if (error) {
    return <div className="p-8 text-red-500">Error: {error.message}</div>;
  }

  return (
    <main className="max-w-5xl mx-auto px-6 py-12">
      <h1 className="text-4xl font-bold mb-2">Utah College Baseball</h1>
      <p className="text-gray-600 dark:text-gray-400 mb-10">
        Gear tracker for Utah&apos;s D1 baseball programs.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {(schools ?? []).map((s: School) => (
          <Link
            key={s.id}
            href={`/schools/${s.id}`}
            className="block p-6 rounded-lg border border-gray-200 dark:border-gray-800 hover:border-gray-400 hover:shadow transition"
          >
            <div className="text-xl font-semibold">{s.name}</div>
            <div className="text-sm text-gray-500">
              {s.short_name} · {s.conference}
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}
