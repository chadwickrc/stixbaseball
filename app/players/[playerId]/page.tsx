import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { supabase, type Player, type School } from "@/lib/supabase";

export const revalidate = 60;

type PlayerWithSchool = Player & { schools: School | null };

export default async function PlayerPage({
  params,
}: {
  params: Promise<{ playerId: string }>;
}) {
  const { playerId } = await params;

  const { data: player } = await supabase
    .from("players")
    .select("*, schools(*)")
    .eq("id", playerId)
    .single<PlayerWithSchool>();

  if (!player) notFound();

  const school = player.schools;
  const bt = fmtBT(player.bats, player.throws);

  return (
    <main className="max-w-4xl mx-auto px-6 py-8">
      <div className="mb-4 text-sm text-gray-500">
        <Link href="/" className="hover:text-gray-900 dark:hover:text-white">
          All schools
        </Link>
        {school ? (
          <>
            <span className="mx-2">/</span>
            <Link
              href={`/schools/${school.id}`}
              className="hover:text-gray-900 dark:hover:text-white"
            >
              {school.name}
            </Link>
          </>
        ) : null}
      </div>

      <div className="flex flex-col sm:flex-row gap-8 mb-10">
        <div className="relative w-48 h-48 sm:w-56 sm:h-56 bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden flex-shrink-0">
          {player.headshot_url ? (
            <Image
              src={player.headshot_url}
              alt={player.name}
              fill
              sizes="224px"
              className="object-cover"
              priority
            />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400 text-5xl">
              {initials(player.name)}
            </div>
          )}
        </div>

        <div className="flex-1">
          <div className="text-sm text-gray-500 mb-1">
            #{player.jersey || "--"}
            {school ? " \u00B7 " + school.name : ""}
          </div>
          <h1 className="text-4xl font-bold mb-2">{player.name}</h1>
          <div className="text-lg text-gray-600 dark:text-gray-400 mb-6">
            {player.position || ""}
            {player.class_year ? " \u00B7 " + player.class_year : ""}
          </div>

          <dl className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
            <InfoRow label="Bats / Throws" value={bt} />
            <InfoRow label="Height" value={player.height} />
            <InfoRow label="Weight" value={player.weight} />
            <InfoRow label="Hometown" value={player.hometown} />
            <InfoRow label="High School" value={player.high_school} />
            <InfoRow label="Previous School" value={player.previous_school} />
          </dl>
        </div>
      </div>

      <section className="border-t border-gray-200 dark:border-gray-800 pt-8">
        <h2 className="text-xl font-semibold mb-4">Gear Used</h2>
        <div className="p-6 rounded-lg border border-dashed border-gray-300 dark:border-gray-700 text-gray-500 text-sm">
          No gear sightings yet. Gear tracking coming soon.
        </div>
      </section>

      {player.profile_url ? (
        <div className="mt-8 text-xs text-gray-500"><a
            href={player.profile_url}
            target="_blank"
            rel="noreferrer"
            className="hover:text-gray-900 dark:hover:text-white underline"
          >
            View official profile
          </a>
        </div>
      ) : null}
    </main>
  );
}

function initials(name: string): string {
  return name
    .split(" ")
    .map((s) => s[0])
    .slice(0, 2)
    .join("");
}

function fmtBT(b: string | null, t: string | null): string | null {
  if (!b && !t) return null;
  return (b || "?") + "/" + (t || "?");
}

function InfoRow({ label, value }: { label: string; value: string | null }) {
  return (
    <>
      <dt className="text-gray-500">{label}</dt>
      <dd className="font-medium">{value || "\u2014"}</dd>
    </>
  );
}
