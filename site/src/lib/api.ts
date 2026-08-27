// db.py 와 똑같은 일을 하는 자바스크립트판입니다.
// 웹(여기) 과 봇(파이썬) 이 같은 표를 씁니다.
import { sb, Place, Driver, Ride } from "./supabase";

const 아무거나 = (v?: string) => !v || v === "dontcare";

export type 조건 = {
  domain: string;
  area?: string; category?: string; price?: string;
  gym?: boolean; parking?: boolean; breakfast?: boolean;
};

export async function searchPlaces(c: 조건): Promise<Place[]> {
  let q = sb.from("places").select("*").eq("domain", c.domain);
  if (!아무거나(c.area)) q = q.eq("area", c.area!);
  if (!아무거나(c.category)) q = q.eq("category", c.category!);
  if (!아무거나(c.price)) q = q.eq("price", c.price!);
  // 체크를 켰을 때만 거릅니다. 끄면 '없어도 된다' 는 뜻이라 안 거릅니다.
  // 시나리오 1 "헬스장 있는 숙소" -> "없어도 돼요" 가 이 줄입니다.
  if (c.gym) q = q.eq("gym", true);
  if (c.parking) q = q.eq("parking", true);
  if (c.breakfast) q = q.eq("breakfast", true);
  const { data } = await q.order("id");
  return data ?? [];
}

export function makeBookingCode() {
  const 글자 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  return Array.from({ length: 5 }, () =>
    글자[Math.floor(Math.random() * 글자.length)]).join("");
}

async function pickDriver(vehicleType = "dontcare", excludeId?: number | null) {
  let q = sb.from("drivers").select("*").eq("is_available", true);
  // dontcare 면 차종을 안 따집니다. 실제 데이터의 94% 가 이 경우입니다.
  if (!아무거나(vehicleType)) q = q.eq("vehicle_type", vehicleType);
  const { data } = await q;
  const rows = (data ?? []).filter((d: Driver) => d.id !== excludeId);
  return rows[0] ?? null;
}

export async function getDriver(id: number | null) {
  if (!id) return null;
  const { data } = await sb.from("drivers").select("*").eq("id", id).single();
  return (data as Driver) ?? null;
}

export async function createRide(v: {
  pickup: string; dropoff: string; requestTime: string; vehicleType: string;
  placeDomain?: string | null;
  placeName?: string | null; placeBooking?: string | null; carried: boolean;
}): Promise<Ride> {
  const driver = await pickDriver(v.vehicleType);
  const { data } = await sb.from("rides").insert({
    place_domain: v.placeDomain ?? null,
    place_name: v.placeName ?? null,
    place_booking: v.placeBooking ?? null,
    carried: v.carried,
    pickup: v.pickup, dropoff: v.dropoff,
    request_time: v.requestTime,
    vehicle_type: v.vehicleType || "dontcare",
    source: "web",
    status: driver ? "배차완료" : "접수",
    driver_id: driver?.id ?? null,
  }).select().single();
  return data as Ride;
}

export async function getRide(id: number) {
  const { data } = await sb.from("rides").select("*").eq("id", id).single();
  return (data as Ride) ?? null;
}

// 9개 시나리오가 전부 이 함수로 옵니다.
export async function updateRide(
  id: number, changes: Partial<Ride>, newDriver = false
): Promise<Ride> {
  const now = await getRide(id);
  const fields: Record<string, unknown> = { ...changes };
  const wantType = (changes.vehicle_type ?? now!.vehicle_type) as string;
  if (newDriver || (changes.vehicle_type && changes.vehicle_type !== now!.vehicle_type)) {
    const d = await pickDriver(wantType, newDriver ? now!.driver_id : null);
    fields.driver_id = d?.id ?? null;
    fields.status = d ? "배차완료" : "접수";
  }
  fields.change_count = (now?.change_count ?? 0) + 1;
  fields.updated_at = new Date().toISOString();
  const { data } = await sb.from("rides").update(fields).eq("id", id).select().single();
  return data as Ride;
}

export async function cancelRide(id: number) {
  const { data } = await sb.from("rides").update({ status: "취소" })
    .eq("id", id).select().single();
  return data as Ride;
}

export async function recentRides(limit = 10): Promise<Ride[]> {
  const { data } = await sb.from("rides").select("*")
    .order("id", { ascending: false }).limit(limit);
  return data ?? [];
}
