import { Badge } from "@/components/ui/badge";

// Gradio 는 계속 켜져 있어야 하는 서버라 버셀에서 못 돕니다.
// 그래서 딴 데서 돌리고 화면만 여기에 끼워 넣습니다.
// ?__theme=light 를 붙여야 iframe 안에서 밝은 화면으로 뜹니다.
// 안 붙이면 보는 사람 브라우저 설정을 따라가 새까맣게 나옵니다(260827 실측).
const RAW = process.env.NEXT_PUBLIC_BOT_URL;
const BOT = RAW ? `${RAW.replace(/\/$/, "")}/?__theme=light` : undefined;

export default function BotPage() {
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
        <p className="py-16 text-center text-sm text-muted-foreground">
          봇 주소가 설정되지 않았습니다. NEXT_PUBLIC_BOT_URL 을 넣어주세요.
        </p>
      )}
    </div>
  );
}
