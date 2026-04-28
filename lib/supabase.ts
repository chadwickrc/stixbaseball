import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!;

export const supabase = createClient(url, key);

export type School = {
  id: string;
  name: string;
  short_name: string | null;
  conference: string | null;
  roster_url: string | null;
  stats_url: string | null;
  instagram: string | null;
};

export type Player = {
  id: string;
  school_id: string;
  jersey: string | null;
  name: string;
  position: string | null;
  bats: string | null;
  throws: string | null;
  height: string | null;
  weight: string | null;
  class_year: string | null;
  hometown: string | null;
  high_school: string | null;
  previous_school: string | null;
  profile_url: string | null;
  headshot_url: string | null;
};
