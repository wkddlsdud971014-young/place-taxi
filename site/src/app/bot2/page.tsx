"use client";

// ================================================================
//  봇2 - 대화가 곧 기록
//
//  왼쪽은 내 컴퓨터에서 도는 파이썬(Gradio), 오른쪽은 이 Next.js 페이지입니다.
//  둘은 서로 말을 주고받지 않습니다. 그런데도 왼쪽에서 대화하면
//  오른쪽이 채워집니다. 같은 창고(Supabase sessions)를 보기 때문입니다.
//  "데이터가 대화 밖에 산다" 를 눈으로 보여주는 화면입니다.
// ================================================================
import { useCallback, useEffect, useState } from "react";
import { getSession, getSetting } from "@/lib/api";
import type { Session } from "@/lib/supabase";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableRow } from "@/components/ui/table";

const 칸 = [
  { key: "place_kind", label: "장소-종류", icon: "🍽️" },
  { key: "place_name", label: "장소-이름", icon: "🍽️" },
  { key: "pickup", label: "택시-출발지", icon: "🚕" },
  { key: "dropoff", label: "택시-도착지", icon: "🚕" },
  { key: "request_time", label: "택시-출발시간", icon: "🚕" },
] as const;

export default function Bot2Page() {
  const [코드, set코드] = useState("1");
  const [메모, set메모] = useState<Session | null>(null);
  const [봇주소, set봇주소] = useState<string | null>(null);
  const [잰때, set잰때] = useState("");

  // 봇 주소는 창고에서 읽습니다. 코드에 안 박아둔 이유는
  // gradio 공개 주소가 72시간마다 바뀌기 때문입니다(260828).
  useEffect(() => {
    getSetting("bot2_url").then(set봇주소).catch(() => set봇주소(null));
  }, []);

  const 읽기 = useCallback(async () => {
    try {
      set메모(await getSession(코드));
      set잰때(new Date().toLocaleTimeString("ko-KR"));
    } catch {
      /* 창고가 잠깐 안 되어도 화면은 그대로 둡니다 */
    }
  }, [코드]);

  // 2초마다 창고를 다시 읽습니다. 봇이 적으면 여기가 따라옵니다.
  useEffect(() => {
    읽기();
    const t = setInterval(읽기, 2000);
    return () => clearInterval(t);
  }, [읽기]);

  const 찬것 = 메모 ? 칸.filter((c) => 메모[c.key]).length : 0;
  const 봇 = 봇주소 ? `${봇주소.replace(/\/$/, "")}/?__theme=light` : null;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-end gap-4">
        <div className="w-32">
          <Label htmlFor="code" className="text-xs">입장 코드</Label>
          <Input id="code" value={코드} onChange={(e) => set코드(e.target.value)} />
        </div>
        <p className="pb-2 text-sm text-muted-foreground">
          왼쪽은 내 컴퓨터에서 도는 파이썬, 오른쪽은 이 웹사이트입니다.{" "}
          <b>둘은 서로 말을 주고받지 않습니다.</b> 같은 창고를 볼 뿐입니다.
        </p>
      </div>

      <div className="grid gap-3 lg:grid-cols-5">
        <div className="lg:col-span-3">
          {봇 ? (
            <iframe
              src={봇}
              className="h-[560px] w-full rounded-xl border bg-white"
              title="봇2"
            />
          ) : (
            <div className="flex h-[560px] flex-col items-center justify-center gap-2 rounded-xl border bg-muted/30 p-8 text-center text-sm text-muted-foreground">
              <span>봇2 가 꺼져 있습니다.</span>
              <code className="rounded bg-background px-2 py-1">
                SHARE=1 ./.venv/bin/python bot2.py
              </code>
              <span>로 켜면 봇이 스스로 주소를 창고에 적고 이 자리에 나타납니다.</span>
            </div>
          )}
        </div>

        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center justify-between text-base">
              <span>🧾 영수증</span>
              <Badge variant={찬것 === 5 ? "default" : "secondary"}>{찬것}/5</Badge>
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              메모판 = Supabase · 2초마다 다시 읽음{잰때 && ` · ${잰때}`}
            </p>
          </CardHeader>
          <CardContent className="space-y-3">
            <Table>
              <TableBody>
                {칸.map((c) => {
                  const v = 메모?.[c.key] ?? null;
                  const 이월 = c.key === "dropoff" && 메모?.carried && !!v;
                  return (
                    <TableRow key={c.key}>
                      <TableCell className="w-8">{c.icon}</TableCell>
                      <TableCell className="text-muted-foreground">{c.label}</TableCell>
                      <TableCell className="text-right font-medium">
                        {v ? (
                          <span className={이월 ? "text-blue-700" : ""}>
                            {이월 && "🔵 "}
                            {v}
                          </span>
                        ) : (
                          <span className="text-muted-foreground/40">—</span>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>

            <p className="text-xs text-muted-foreground">
              말한 횟수 <b>{메모?.turns ?? 0}회</b> · Gemini 호출 <b>매번 1콜</b> ·
              프롬프트 길이 <b>안 늘어남</b>
            </p>

            {메모?.ride_id ? (
              <div className="rounded-lg border border-green-600/30 bg-green-50 p-3 text-sm">
                <b className="text-green-800">영수증 발행됨</b>
                <div className="text-green-900/80">호출번호 {메모.ride_id}</div>
              </div>
            ) : null}

            {메모?.carried ? (
              <div className="rounded-lg border border-blue-600/30 bg-blue-50 p-3 text-xs text-blue-900">
                🔵 도착지를 손님이 다시 말하지 않았습니다. 장소에서 이월됐습니다.
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <p className="text-xs text-muted-foreground">
        브라우저를 껐다 켜도 같은 입장 코드를 넣으면 그대로 돌아옵니다. 슬롯이 봇 안이
        아니라 창고에 있기 때문입니다.
      </p>
    </div>
  );
}
