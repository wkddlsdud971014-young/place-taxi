"use client";

import { useEffect, useState } from "react";
import {
  searchPlaces, makeBookingCode, createRide, updateRide,
  cancelRide, recentRides, getDriver,
} from "@/lib/api";
import type { Place, Ride, Driver } from "@/lib/supabase";
import { Steps } from "@/components/nav";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle,
} from "@/components/ui/card";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

const 지역들 = ["상관없음", "서울 중앙", "서울 동쪽", "서울 서쪽", "서울 남쪽", "서울 북쪽"];
const 가격들 = ["상관없음", "저렴", "보통", "비싼", "무료"];
const 차종들 = ["아무거나", "일반", "고급", "대형"];

// 도메인마다 고를 수 있는 종류와 조건이 다릅니다
const 도메인들 = [
  { key: "식당", icon: "🍽️", 종류: ["상관없음", "한식", "중식", "일식", "양식", "치킨"],
    조건: [{ key: "parking", label: "주차 가능" }] },
  { key: "숙소", icon: "🏨", 종류: ["상관없음", "호텔", "모텔", "게스트하우스"],
    조건: [{ key: "gym", label: "헬스장" }, { key: "breakfast", label: "조식" },
           { key: "parking", label: "주차 가능" }] },
  { key: "관광", icon: "🏛️", 종류: ["상관없음", "역사", "자연", "쇼핑"],
    조건: [{ key: "parking", label: "주차 가능" }] },
] as const;

const toDb = (v: string) => (v === "상관없음" || v === "아무거나" ? "dontcare" : v);
const toUi = (v: string) => (v === "dontcare" ? "아무거나" : v);

export default function Home() {
  // 1번 블록
  const [도메인, set도메인] = useState<"식당" | "숙소" | "관광">("식당");
  const [area, setArea] = useState("상관없음");
  const [cate, setCate] = useState("상관없음");
  const [price, setPrice] = useState("상관없음");
  const [옵션, set옵션] = useState<Record<string, boolean>>({});
  const [후보, set후보] = useState<Place[]>([]);
  const [고른것, set고른것] = useState<string>("");
  const [식당, set식당] = useState<Place | null>(null);
  const [예약번호, set예약번호] = useState<string>("");
  const 지금도메인 = 도메인들.find((d) => d.key === 도메인)!;

  // 2번 블록
  const [pickup, setPickup] = useState("");
  const [dropoff, setDropoff] = useState("");
  const [time, setTime] = useState("");
  const [vtype, setVtype] = useState("아무거나");

  const [ride, setRide] = useState<Ride | null>(null);
  const [기사, set기사] = useState<Driver | null>(null);
  const [안내, set안내] = useState("");
  const [수정중, set수정중] = useState<string | null>(null);   // 장바구니처럼 한 줄씩 고칩니다
  const [임시값, set임시값] = useState("");
  const [목록, set목록] = useState<Ride[]>([]);
  const [바쁨, set바쁨] = useState(false);

  const 목록새로 = async () => set목록(await recentRides(10));
  useEffect(() => { 목록새로(); }, []);

  const 보이기 = async (r: Ride | null) => {
    setRide(r);
    set기사(r ? await getDriver(r.driver_id) : null);
    // 인라인으로 고친 값을 위쪽 폼에도 반영합니다. 안 하면 둘이 따로 놉니다.
    if (r) {
      setPickup(r.pickup ?? ""); setDropoff(r.dropoff ?? "");
      setTime(r.request_time ?? ""); setVtype(toUi(r.vehicle_type));
    }
    await 목록새로();
  };

  // ---------- 장바구니식 한 줄 수정 ----------
  // 폼 전체를 다시 채우지 않고 그 칸 하나만 고칩니다.
  const 한줄저장 = async (key: string, val: string) => {
    if (!ride) return;
    const changes: Record<string, unknown> = {
      [key]: key === "vehicle_type" ? toDb(val) : val,
    };
    if (key === "dropoff") changes.carried = !!식당 && val === 식당.name;
    set바쁨(true);
    const r = await updateRide(ride.id, changes);
    await 보이기(r);
    set수정중(null);
    set안내(`${key === "pickup" ? "출발지" : key === "dropoff" ? "도착지"
            : key === "request_time" ? "출발시간" : "차종"} 하나만 고쳤습니다.`);
    set바쁨(false);
  };

  // ---------- 1번 블록 ----------
  const 검색 = async () => {
    set바쁨(true);
    const rows = await searchPlaces({
      domain: 도메인, area: toDb(area), category: toDb(cate), price: toDb(price),
      gym: 옵션.gym, parking: 옵션.parking, breakfast: 옵션.breakfast,
    });
    set후보(rows);
    set고른것(rows[0]?.name ?? "");
    set안내(rows.length ? `${도메인} ${rows.length}곳 찾았습니다.`
                        : `조건에 맞는 ${도메인}이(가) 없습니다. 조건을 풀어보세요.`);
    set바쁨(false);
  };

  // 도메인을 바꾸면 조건과 후보를 비웁니다 (시나리오 9)
  const 도메인바꾸기 = (d: "식당" | "숙소" | "관광") => {
    set도메인(d); setCate("상관없음"); setPrice("상관없음");
    set옵션({}); set후보([]); set고른것("");
  };

  // 시나리오 9 - 처음부터 다시
  const 처음부터 = async () => {
    if (ride) await cancelRide(ride.id);
    set도메인("식당"); setArea("상관없음"); setCate("상관없음"); setPrice("상관없음");
    set옵션({}); set후보([]); set고른것(""); set식당(null); set예약번호("");
    setPickup(""); setDropoff(""); setTime(""); setVtype("아무거나");
    setRide(null); set기사(null); set수정중(null);
    set안내("처음부터 다시 시작합니다.");
    await 목록새로();
  };

  const 예약 = async () => {
    const 가게 = 후보.find((r) => r.name === 고른것);
    if (!가게) return set안내("먼저 장소를 검색해서 하나 고르세요.");
    set바쁨(true);
    const code = makeBookingCode();
    set식당(가게); set예약번호(code);
    setDropoff(가게.name);           // ★ 이월 ★ 도착지가 저절로 채워집니다
    if (ride) {
      const r = await updateRide(ride.id, {
        dropoff: 가게.name, place_domain: 도메인, place_name: 가게.name,
        place_booking: code, carried: true,
      });
      await 보이기(r);
      set안내(`${가게.name} 예약 완료 · 이미 부른 택시의 도착지도 같이 바꿨습니다.`);
    } else {
      set안내(`${가게.name} 예약 완료 · 예약번호 ${code} · 도착지로 이월했습니다.`);
    }
    set바쁨(false);
  };

  // ---------- 2번 블록 ----------
  const 부르기 = async () => {
    if (!pickup || !dropoff) return set안내("출발지와 도착지를 채워주세요.");
    set바쁨(true);
    const r = await createRide({
      pickup, dropoff, requestTime: time, vehicleType: toDb(vtype),
      placeDomain: 식당 ? 도메인 : null,
      placeName: 식당?.name ?? null, placeBooking: 예약번호 || null,
      carried: !!식당 && dropoff === 식당.name,
    });
    await 보이기(r);
    set안내(`배차했습니다. 호출번호 ${r.id}`);
    set바쁨(false);
  };

  const 변경저장 = async () => {
    if (!ride) return set안내("먼저 [택시 부르기] 를 눌러주세요.");
    const 새값: Record<string, string> = {
      pickup, dropoff, request_time: time, vehicle_type: toDb(vtype),
    };
    const 바뀐것: Record<string, unknown> = {};
    (Object.keys(새값) as (keyof Ride)[]).forEach((k) => {
      if (새값[k as string] !== (ride[k] as string)) 바뀐것[k] = 새값[k as string];
    });
    if (!Object.keys(바뀐것).length) return set안내("바뀐 것이 없습니다.");
    if ("dropoff" in 바뀐것) 바뀐것.carried = !!식당 && 바뀐것.dropoff === 식당.name;
    set바쁨(true);
    const r = await updateRide(ride.id, 바뀐것);
    await 보이기(r);
    const 이름 = { pickup: "출발지", dropoff: "도착지", request_time: "출발시간", vehicle_type: "차종" } as Record<string, string>;
    set안내(`바꾼 칸 — ${Object.keys(바뀐것).filter((k) => 이름[k]).map((k) => 이름[k]).join(", ")}`);
    set바쁨(false);
  };

  const 기사변경 = async () => {
    if (!ride) return set안내("먼저 [택시 부르기] 를 눌러주세요.");
    set바쁨(true);
    await 보이기(await updateRide(ride.id, {}, true));
    set안내("다른 기사로 다시 배차했습니다.");
    set바쁨(false);
  };

  const 취소 = async () => {
    if (!ride) return;
    set바쁨(true);
    await cancelRide(ride.id);
    await 보이기(null);
    set안내("취소했습니다.");
    set바쁨(false);
  };

  const 지금단계: 1 | 2 | 3 = ride ? 3 : 식당 ? 2 : 1;

  return (
    <div className="space-y-6">
      <Steps 지금={지금단계} />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* ---------------- 1번 블록 ---------------- */}
        <Card className="tab-place">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <span className="text-lg">{지금도메인.icon}</span>
              <CardTitle className="text-base">BLOCK 1 · 장소 접수</CardTitle>
              {식당 && <Badge className="ml-auto bg-green-600 hover:bg-green-600">예약 완료</Badge>}
            </div>
            <CardDescription>도메인을 고르고 조건을 좁혀 하나를 예약합니다.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 도메인 선택 - 시나리오 9(처음부터 다시, 식당으로) 가 여기입니다 */}
            <div className="grid grid-cols-3 gap-2">
              {도메인들.map((d) => (
                <button key={d.key} type="button" onClick={() => 도메인바꾸기(d.key)}
                  className={`rounded-lg border px-3 py-2.5 text-sm font-medium transition ${
                    도메인 === d.key
                      ? "border-amber-400 bg-amber-50 text-amber-900"
                      : "hover:bg-muted"}`}>
                  <span className="mr-1.5">{d.icon}</span>{d.key}
                </button>
              ))}
            </div>

            <div className="grid grid-cols-3 gap-3">
              {([["지역", area, setArea, 지역들], ["종류", cate, setCate, 지금도메인.종류],
                 ["가격대", price, setPrice, 가격들]] as const).map(([label, val, set, opts]) => (
                <div key={label} className="space-y-1.5">
                  <Label className="text-xs">{label}</Label>
                  <Select value={val} onValueChange={(v) => set(v ?? "")}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {opts.map((o) => <SelectItem key={o} value={o}>{o}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              ))}
            </div>

            {/* 켜면 그 조건이 있는 곳만, 끄면 '없어도 된다' 는 뜻 (시나리오 1) */}
            <div className="flex flex-wrap gap-2">
              {지금도메인.조건.map((c) => (
                <button key={c.key} type="button"
                  onClick={() => set옵션((o) => ({ ...o, [c.key]: !o[c.key] }))}
                  className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
                    옵션[c.key]
                      ? "border-blue-400 bg-blue-50 text-blue-800"
                      : "text-muted-foreground hover:bg-muted"}`}>
                  {옵션[c.key] ? "✓ " : ""}{c.label}
                </button>
              ))}
              <span className="self-center text-[11px] text-muted-foreground">
                켜면 그 조건이 있는 곳만 · 끄면 상관없음
              </span>
            </div>

            <Button variant="outline" className="w-full" onClick={검색} disabled={바쁨}>
              {도메인} 검색
            </Button>

            {후보.length > 0 && (
              <RadioGroup value={고른것} onValueChange={set고른것} className="gap-0 rounded-lg border">
                {후보.map((r, i) => (
                  <label key={r.id}
                    className={`flex cursor-pointer items-center gap-3 px-3 py-2.5 text-sm ${i ? "border-t" : ""}`}>
                    <RadioGroupItem value={r.name} />
                    <span className="font-medium">{r.name}</span>
                    <span className="ml-auto text-xs text-muted-foreground">
                      {r.area} · {r.category}{r.price ? ` · ${r.price}` : ""}
                    </span>
                  </label>
                ))}
              </RadioGroup>
            )}

            <Button className="w-full" onClick={예약} disabled={바쁨 || !고른것}>
              이 장소 예약
            </Button>

            {식당 && (
              <div className="rounded-lg border bg-muted/40 p-3 text-sm">
                <div className="font-medium">{식당.name}</div>
                <div className="mt-1 text-xs text-muted-foreground">
                  {식당.area} · {식당.category}{식당.price ? ` · ${식당.price}` : ""} · {식당.phone}
                  <br />예약번호 <span className="font-mono">{예약번호}</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* ---------------- 2번 블록 ---------------- */}
        <Card className="tab-taxi">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <span className="text-lg">🚕</span>
              <CardTitle className="text-base">BLOCK 2 · 택시 배차</CardTitle>
              {ride && <Badge className="ml-auto bg-green-600 hover:bg-green-600">{ride.status}</Badge>}
            </div>
            <CardDescription>
              장소를 예약하면 <span className="font-medium text-foreground">도착지가 저절로 채워집니다</span>.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {식당 && dropoff === 식당.name && (
              <div className="carry-box rounded-lg px-3 py-2.5 text-xs">
                <span className="font-semibold">🔵 도착지 자동 이월됨</span>
                <br />
                앞서 예약한 <span className="font-semibold">{식당.name}</span> 이(가) 도착지로 자동
                지정되었습니다. 아래 칸에서 직접 고칠 수도 있습니다.
              </div>
            )}
            <div className="space-y-1.5">
              <Label className="text-xs">출발지</Label>
              <Input value={pickup} onChange={(e) => setPickup(e.target.value)} placeholder="강남역" />
            </div>
            <div className="space-y-1.5">
              <Label className="flex items-center gap-1.5 text-xs">
                도착지
                {식당 && dropoff === 식당.name && (
                  <Badge variant="secondary" className="h-5 px-1.5 text-[10px] font-medium">
                    식당에서 이월됨
                  </Badge>
                )}
              </Label>
              <Input value={dropoff} onChange={(e) => setDropoff(e.target.value)}
                     className={식당 && dropoff === 식당.name ? "carry-input" : ""}
                     placeholder="장소를 예약하면 채워집니다" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">출발 시간</Label>
              <Input value={time} onChange={(e) => setTime(e.target.value)} placeholder="19:00" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">차종</Label>
              <RadioGroup value={vtype} onValueChange={setVtype} className="flex gap-4 pt-1">
                {차종들.map((t) => (
                  <label key={t} className="flex cursor-pointer items-center gap-1.5 text-sm">
                    <RadioGroupItem value={t} />{t}
                  </label>
                ))}
              </RadioGroup>
            </div>

            <Button className="w-full" onClick={부르기} disabled={바쁨}>택시 부르기</Button>

            <Separator />
            <p className="text-xs text-muted-foreground">
              접수한 뒤 고칠 때 — 위 칸을 고치고 아래를 누르세요.
            </p>
            <div className="grid grid-cols-3 gap-2">
              <Button variant="outline" size="sm" onClick={변경저장} disabled={바쁨}>변경 저장</Button>
              <Button variant="outline" size="sm" onClick={기사변경} disabled={바쁨}>다른 기사로</Button>
              <Button variant="outline" size="sm" onClick={취소} disabled={바쁨}>취소</Button>
            </div>
            {/* 시나리오 9 - 다 정한 뒤 처음부터 다시 */}
            <Button variant="ghost" size="sm" className="w-full text-xs text-muted-foreground"
                    onClick={처음부터} disabled={바쁨}>
              ✨ 처음부터 다시
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* ---------------- 결과 ---------------- */}
      {(ride || 안내) && (
        <Card className={ride ? "tab-done done-box" : ""}>
          <CardHeader className="pb-3">
            <div className="flex flex-wrap items-center gap-2">
              {ride && <span className="text-lg">✅</span>}
              <CardTitle className="text-base">
                {ride ? `배차 확정 · TX-${String(ride.id).padStart(5, "0")}` : "안내"}
              </CardTitle>
              {ride && <Badge className="bg-green-600 hover:bg-green-600">{ride.status}</Badge>}
              {ride?.carried && (
                <Badge className="bg-blue-600 hover:bg-blue-600">도착지 이월됨</Badge>
              )}
              {ride && <Badge variant="outline">고친 횟수 {ride.change_count}</Badge>}
            </div>
            {안내 && <CardDescription>{안내}</CardDescription>}
          </CardHeader>
          {ride && (
            <CardContent className="space-y-0">
              <div className="rounded-lg border">
                {([
                  { key: "place_name",
                    label: ride.place_domain ?? "장소",
                    val: ride.place_name ?? "-", 고칠수있나: false },
                  { key: "pickup", label: "출발지", val: ride.pickup ?? "", 고칠수있나: true },
                  { key: "dropoff", label: "도착지", val: ride.dropoff ?? "", 고칠수있나: true },
                  { key: "request_time", label: "출발시간", val: ride.request_time ?? "", 고칠수있나: true },
                  { key: "vehicle_type", label: "차종", val: toUi(ride.vehicle_type), 고칠수있나: true },
                ]).map((행, i) => (
                  <div key={행.key}
                       className={`flex items-center gap-3 px-3 py-2.5 text-sm ${i ? "border-t" : ""}`}>
                    <span className="w-20 shrink-0 text-xs text-muted-foreground">{행.label}</span>
                    {수정중 === 행.key ? (
                      <>
                        {행.key === "vehicle_type" ? (
                          <Select value={임시값} onValueChange={(v) => set임시값(v ?? "")}>
                            <SelectTrigger className="h-8 flex-1"><SelectValue /></SelectTrigger>
                            <SelectContent>
                              {차종들.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                            </SelectContent>
                          </Select>
                        ) : (
                          <Input className="h-8 flex-1" value={임시값} autoFocus
                                 onChange={(e) => set임시값(e.target.value)}
                                 onKeyDown={(e) => { if (e.key === "Enter") 한줄저장(행.key, 임시값); }} />
                        )}
                        <Button size="sm" className="h-8" disabled={바쁨}
                                onClick={() => 한줄저장(행.key, 임시값)}>저장</Button>
                        <Button size="sm" variant="ghost" className="h-8"
                                onClick={() => set수정중(null)}>취소</Button>
                      </>
                    ) : (
                      <>
                        <span className="flex-1 font-medium">
                          {행.val || <span className="text-muted-foreground">-</span>}
                          {행.key === "dropoff" && ride.carried && (
                            <Badge variant="secondary" className="ml-2 h-5 px-1.5 text-[10px]">이월</Badge>
                          )}
                        </span>
                        {행.고칠수있나 && (
                          <Button size="sm" variant="ghost" className="h-7 px-2 text-xs"
                                  onClick={() => { set수정중(행.key); set임시값(행.val); }}>
                            수정
                          </Button>
                        )}
                      </>
                    )}
                  </div>
                ))}
                <div className="flex items-center gap-3 border-t px-3 py-2.5 text-sm">
                  <span className="w-20 shrink-0 text-xs text-muted-foreground">기사</span>
                  <span className="flex-1 font-medium">
                    {기사 ? `${기사.name} · ${기사.phone} · ${기사.vehicle_type}` : "배차 대기중"}
                  </span>
                  <Button size="sm" variant="ghost" className="h-7 px-2 text-xs"
                          onClick={기사변경} disabled={바쁨}>바꾸기</Button>
                </div>
              </div>
              <p className="pt-3 text-xs text-muted-foreground">
                줄마다 <span className="font-medium text-foreground">수정</span> 을 눌러 하나씩 고치거나,
                위쪽 폼을 고치고 <span className="font-medium text-foreground">변경 저장</span> 으로 여러 칸을 한 번에 고칩니다.
              </p>
            </CardContent>
          )}
        </Card>
      )}

      {/* ---------------- 최근 호출 ---------------- */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">📊 최근 호출</CardTitle>
          <CardDescription>웹과 봇이 같은 창고를 씁니다. 둘이 섞여서 쌓입니다.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  {["번호", "어디서", "도메인", "장소", "출발지", "도착지", "이월", "시간", "차종", "상태", "고친횟수"]
                    .map((h) => <TableHead key={h} className="text-xs">{h}</TableHead>)}
                </TableRow>
              </TableHeader>
              <TableBody>
                {목록.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="font-mono text-xs">{r.id}</TableCell>
                    <TableCell>
                      <Badge variant={r.source === "bot" ? "default" : "secondary"}
                             className="h-5 px-1.5 text-[10px]">{r.source}</Badge>
                    </TableCell>
                    <TableCell className="text-xs">{r.place_domain ?? "-"}</TableCell>
                    <TableCell className="text-xs">{r.place_name ?? "-"}</TableCell>
                    <TableCell className="text-xs">{r.pickup}</TableCell>
                    <TableCell className="text-xs">{r.dropoff}</TableCell>
                    <TableCell className="text-xs">{r.carried ? "●" : ""}</TableCell>
                    <TableCell className="text-xs">{r.request_time}</TableCell>
                    <TableCell className="text-xs">{toUi(r.vehicle_type)}</TableCell>
                    <TableCell className="text-xs">{r.status}</TableCell>
                    <TableCell className="text-xs tabular-nums">{r.change_count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
