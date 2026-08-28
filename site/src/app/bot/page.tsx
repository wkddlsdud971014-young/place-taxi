"use client";

// Gradio 는 계속 켜져 있어야 하는 서버라 버셀에서 못 돕니다.
// 그래서 딴 데서 돌리고 화면만 여기에 끼워 넣습니다.
// ?__theme=light 를 붙여야 iframe 안에서 밝은 화면으로 뜹니다.
// 안 붙이면 보는 사람 브라우저 설정을 따라가 새까맣게 나옵니다(260827 실측).
//
// 주소는 창고(settings 표)에서 읽습니다. 예전에는 NEXT_PUBLIC_BOT_URL 에
// 박아두었는데, gradio 공개 주소가 72시간마다 죽어서 그때마다 다시
// 배포해야 했습니다. 이제 봇이 켜질 때 스스로 주소를 적습니다(260828).
import { useEffect, useState } from "react";
import { getSetting } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

export default function BotPage() {
  const [주소, set주소] = useState<string | null>(null);
  const [읽는중, set읽는중] = useState(true);

  useEffect(() => {
    getSetting("bot_url")
      .then((v) => set주소(v ?? process.env.NEXT_PUBLIC_BOT_URL ?? null))
      .catch(() => set주소(process.env.NEXT_PUBLIC_BOT_URL ?? null))
      .finally(() => set읽는중(false));
  }, []);

  const BOT = 주소 ? `${주소.replace(/\/$/, "")}/?__theme=light` : undefined;

  return (
    <div className="space-y-3">
      {/* 안내를 한 줄로 줄였습니다. 길면 채팅창이 아래로 밀려
          스크롤을 한참 내려야 했습니다(260827 실측). */}
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Badge variant="secondary">Gradio</Badge>
        <span className="text-muted-foreground">
          &ldquo;헬스장 있는 숙소 찾아줘&rdquo; → &ldquo;1번&rdquo; → &ldquo;강남역에서 19시에 택시&rdquo;
        </span>
        <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-800">
          🔵 &ldquo;거기로 가는 택시&rdquo; 도 알아들음
        </span>
      </div>

      {BOT ? (
        <iframe
          src={BOT}
          // 화면 높이에 맞춰 늘어납니다. 바깥 스크롤 없이 채팅창이 바로 보입니다.
          className="h-[560px] w-full rounded-xl border bg-white"
          title="Gradio 봇"
        />
      ) : (
        <div className="flex h-[560px] flex-col items-center justify-center gap-2 rounded-xl border bg-muted/30 p-8 text-center text-sm text-muted-foreground">
          {읽는중 ? (
            <span>봇 주소를 읽는 중입니다…</span>
          ) : (
            <>
              <span>봇이 꺼져 있습니다.</span>
              <code className="rounded bg-background px-2 py-1">
                SHARE=1 ./.venv/bin/python bot.py
              </code>
              <span>로 켜면 봇이 스스로 주소를 창고에 적고 이 자리에 나타납니다.</span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
