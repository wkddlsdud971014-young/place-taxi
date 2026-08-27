import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// Gradio 는 계속 켜져 있어야 하는 서버라 버셀에서 못 돕니다.
// 그래서 딴 데서 돌리고 화면만 여기에 끼워 넣습니다.
const BOT = process.env.NEXT_PUBLIC_BOT_URL;

export default function BotPage() {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">말로 하기</CardTitle>
            <Badge variant="secondary">Gradio</Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            &ldquo;헬스장 있는 숙소 찾아줘&rdquo; → &ldquo;1번&rdquo; →
            &ldquo;강남역에서 19시에 택시&rdquo; 처럼 이어서 말하면 됩니다.
            <br />
            <span className="font-medium text-foreground">
              &ldquo;거기로 가는 택시&rdquo;
            </span>{" "}
            처럼 장소 이름을 다시 말하지 않아도 알아듣습니다.
          </p>
        </CardHeader>
        <CardContent>
          {BOT ? (
            <iframe
              src={BOT}
              className="h-[720px] w-full rounded-lg border bg-background"
              title="Gradio 봇"
            />
          ) : (
            <p className="py-16 text-center text-sm text-muted-foreground">
              봇 주소가 설정되지 않았습니다. NEXT_PUBLIC_BOT_URL 을 넣어주세요.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
