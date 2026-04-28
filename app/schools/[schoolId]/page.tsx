import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { supabase, type School, type Player } from "@/lib/supabase";

export const revalidate = 60;

export default async function SchoolPage({
  params,
}: {
  params: Promise<{ schoolId: string }>;
}) {
  const { schoolId } = await params;

  const { data: school } = await supabase
    .from("schools")
    .select("*")
    .eq("id", schoolId)
    .single<School>();

  if (!school) notFound();

  const { data: players } = await supabase
    .from("players")
    .select("*")
    .eq("school_id", schoolId)
    .order("jersey", { ascending: true });

  return (
    <main className="max-w-6xl mx-auto px-6 py-8">
      <Link
        href="/"
        className="text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white mb-4 inline-block"
      >
        ← All schools
      </Link>

      <h1 className="text-3xl font-bold mb-1">{school.name}</h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">
        {school.conference} · {players?.length ?? 0} players
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {(players ?? []).map((p: Player) => (
          <Link
            key={p.id}
            href={`/players/${p.id}`}
            className="p-4 rounded-lg border border-gray-200 dark:border-gray-800 hover:shadow hover:border-gray-400 transition block"
          >
            <div className="relative w-full aspect-square bg-gray-100 dark:bg-gray-800 rounded mb-3 overflow-hidden">
              {p.headshot_url ? (
                <Image
                  src={p.headshot_url}
                  alt={p.name}
                  fill
                  sizes="200px"
                  className="object-cover"
                />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400 text-3xl">
                  {p.name
                    .split(" ")
                    .map((s) => s[0])
                    .slice(0, 2)
                    .join("")}
                </div>
              )}
            </div>
            <div className="text-xs text-gray-500">#{p.jersey || "--"}</div>
            <div className="font-semibold text-sm truncate">{p.name}</div>
            <div className="text-xs text-gray-500">
              {p.position} · {p.class_year}
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}
