"use client";

import { useEffect, useState } from "react";
import { recentRides } from "@/lib/api";
import { sb } from "@/lib/supabase";
import type { Ride } from "@/lib/supabase";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const 비밀번호 = "0000";
const KEY = "admin-ok";

const toUi = (v: string) => (v === "dontcare" ? "아무거나" : v);

export default function Admin() {
  const [들어옴, set들어옴] = useState(false);
  const [친것, set친것] = useState("");
  const [틀림, set틀림] = useState(false);
  const [목록, set목록] = useState<Ride[]>([]);
  const [바쁨, set바쁨] = useState(false);

  useEffect(() => {
    try { if (sessionStorage.getItem(KEY) === "1") set들어옴(true); } catch {}
  }, []);

  const 새로 = async () => {
    set바쁨(true);
    set목록(await recentRides(100));
    set바쁨(false);
  };
  useEffect(() => { if (들어옴) 새로(); }, [들어옴]);

  const 열기 = () => {
    if (친것 === 비밀번호) {
      set들어옴(true); set틀림(false);
      try { sessionStorage.setItem(KEY, "1"); } catch {}
    } else set틀림(true);
  };

  const 지우기 = async (id: number) => {
    set바쁨(true);
    await sb.from("rides").delete().eq("id", id);
    await 새로();
  };

  const 전부지우기 = async () => {
    if (!confirm("호출 기록을 전부 지웁니다. 계속할까요?")) return;
    set바쁨(true);
    await sb.from("rides").delete().gt("id", 0);
    await 새로();
  };

  // ---------------- 잠금 화면 ----------------
  if (!들어옴) {
    return (
      <div className="mx-auto max-w-sm pt-16">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">🔒 관리자</CardTitle>
            <CardDescription>비밀번호를 넣어주세요.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Input type="password" value={친것} autoFocus
                   onChange={(e) => { set친것(e.target.value); set틀림(false); }}
                   onKeyDown={(e) => { if (e.key === "Enter") 열기(); }}
                   placeholder="••••" />
            {틀림 && <p className="text-xs text-red-600">비밀번호가 맞지 않습니다.</p>}
            <Button className="w-full" onClick={열기}>들어가기</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ---------------- 통계 ----------------
  const n = 목록.length;
  const 웹 = 목록.filter((r) => r.source === "web").length;
  const 봇 = 목록.filter((r) => r.source === "bot").length;
  const 이월 = 목록.filter((r) => r.carried).length;
  const 고침 = 목록.filter((r) => r.change_count > 0).length;
  const 평균고침 = n ? (목록.reduce((a, r) => a + r.change_count, 0) / n).toFixed(1) : "0";

  const 통계 = [
    { label: "전체 호출", val: n },
    { label: "웹 / 봇", val: `${웹} / ${봇}` },
    { label: "도착지 이월", val: n ? `${이월} (${Math.round((이월 / n) * 100)}%)` : "0" },
    { label: "고친 적 있음", val: n ? `${고침} (${Math.round((고침 / n) * 100)}%)` : "0" },
    { label: "평균 고친 횟수", val: 평균고침 },
  ];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-lg font-semibold">🔧 관리자 — 호출 기록</h2>
        <Badge variant="secondary">{n}건</Badge>
        <div className="ml-auto flex gap-2">
          <Button size="sm" variant="outline" onClick={새로} disabled={바쁨}>새로고침</Button>
          <Button size="sm" variant="outline" onClick={전부지우기} disabled={바쁨 || !n}>
            전부 지우기
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        {통계.map((s) => (
          <div key={s.label} className="rounded-xl border bg-card p-3">
            <div className="text-xs text-muted-foreground">{s.label}</div>
            <div className="mt-0.5 text-lg font-semibold tabular-nums">{s.val}</div>
          </div>
        ))}
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  {["번호", "어디서", "도메인", "장소", "예약번호", "출발지", "도착지",
                    "이월", "시간", "차종", "상태", "고친횟수", "만든 때", ""]
                    .map((h) => <TableHead key={h} className="whitespace-nowrap text-xs">{h}</TableHead>)}
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
                    <TableCell className="whitespace-nowrap text-xs">{r.place_domain ?? "-"}</TableCell>
                    <TableCell className="whitespace-nowrap text-xs">{r.place_name ?? "-"}</TableCell>
                    <TableCell className="font-mono text-[11px]">{r.place_booking ?? "-"}</TableCell>
                    <TableCell className="whitespace-nowrap text-xs">{r.pickup}</TableCell>
                    <TableCell className="whitespace-nowrap text-xs">{r.dropoff}</TableCell>
                    <TableCell className="text-center text-xs">{r.carried ? "🔵" : ""}</TableCell>
                    <TableCell className="text-xs">{r.request_time}</TableCell>
                    <TableCell className="text-xs">{toUi(r.vehicle_type)}</TableCell>
                    <TableCell className="whitespace-nowrap text-xs">{r.status}</TableCell>
                    <TableCell className="text-center text-xs tabular-nums">
                      {r.change_count > 0
                        ? <span className="font-semibold">{r.change_count}</span>
                        : <span className="text-muted-foreground">0</span>}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-[11px] text-muted-foreground">
                      {new Date(r.created_at).toLocaleString("ko-KR",
                        { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })}
                    </TableCell>
                    <TableCell>
                      <Button size="sm" variant="ghost" className="h-7 px-2 text-xs"
                              onClick={() => 지우기(r.id)} disabled={바쁨}>삭제</Button>
                    </TableCell>
                  </TableRow>
                ))}
                {!n && (
                  <TableRow>
                    <TableCell colSpan={14} className="py-10 text-center text-sm text-muted-foreground">
                      호출 기록이 없습니다.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground">
        이 비밀번호는 실습용입니다. 화면에서만 막을 뿐이라 진짜 잠금이 아닙니다.
      </p>
    </div>
  );
}
