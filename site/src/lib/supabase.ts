// 창고 연결. 파이썬의 db.py 와 같은 표를 봅니다.
import { createClient } from "@supabase/supabase-js";

export const sb = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export type Place = {
  id: number; domain: string; name: string; area: string;
  category: string; price: string | null; phone: string;
  gym: boolean; parking: boolean; breakfast: boolean;
};

export type Driver = {
  id: number; name: string; phone: string;
  vehicle_type: string; is_available: boolean;
};

export type Ride = {
  id: number;
  place_domain: string | null;
  place_name: string | null;
  place_booking: string | null;
  carried: boolean;
  pickup: string | null;
  dropoff: string | null;
  request_time: string | null;
  vehicle_type: string;
  status: string;
  driver_id: number | null;
  source: string;
  change_count: number;
  created_at: string;
};
