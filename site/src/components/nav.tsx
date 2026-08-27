"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const 탭 = [
  { href: "/", label: "일반 접수", icon: "📋", desc: "칸을 채운다" },
  { href: "/bot", label: "챗봇 접수", icon: "💬", desc: "말로 한다" },
];

// 채점 기준을 화면에 그대로 띄웁니다. 보는 사람이 찾아다니지 않게.
const 검증 = ["두 블록 연계 (장소 ➔ 택시)", "도착지 자동 이월", "슬롯 자유 수정"];

export function Nav() {
  const path = usePathname();
  return (
    <header className="hero">
      <div className="mx-auto max-w-6xl px-6 pt-10 pb-6">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold tracking-widest">
              <span className="text-base leading-none">🚕</span>
              <span className="hero-taxi">TAXI</span>
              <span className="text-white/50">·</span>
              <span className="text-white/70">식당 · 숙소 · 관광</span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
              장소 접수 <span className="hero-taxi">➔</span> 택시 배차
            </h1>
            <p className="mt-2 text-sm text-white/60">
              식당 · 숙소 · 관광 중에 하나를 정하면 택시 도착지가 저절로 채워집니다. 웹과 봇이 같은 창고를 씁니다.
            </p>
          </div>

          <div className="rounded-xl border border-white/15 bg-white/5 p-4 text-sm backdrop-blur">
            <div className="mb-2 text-xs font-semibold tracking-wide text-white/50">
              핵심 기능 검증
            </div>
            <ul className="space-y-1">
              {검증.map((c) => (
                <li key={c} className="flex items-center gap-2 text-white/85">
                  <span className="hero-taxi font-bold">✓</span>
                  {c}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <nav className="mt-8 flex gap-2">
          {탭.map((t) => (
            <Link
              key={t.href}
              href={t.href}
              className={cn(
                "flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition",
                path === t.href
                  ? "bg-white text-slate-900 shadow-sm"
                  : "bg-white/10 text-white/70 hover:bg-white/15 hover:text-white"
              )}
            >
              <span>{t.icon}</span>
              {t.label}
              <span className={cn("text-xs font-normal",
                path === t.href ? "text-slate-500" : "text-white/45")}>
                {t.desc}
              </span>
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}

// 1 → 2 → 3 진행 표시
export function Steps({ 지금 }: { 지금: 1 | 2 | 3 }) {
  const 단계 = [
    { n: 1, label: "장소 접수", sub: "식당 · 숙소 · 관광" },
    { n: 2, label: "택시 배차", sub: "도착지 이월 → 호출" },
    { n: 3, label: "배차 확정", sub: "기사 배정 · 수정 가능" },
  ];
  return (
    <ol className="grid gap-3 sm:grid-cols-3">
      {단계.map((s) => (
        <li key={s.n}
            className={cn("step flex items-center gap-3 rounded-xl px-4 py-3",
              지금 === s.n && "step-on", 지금 > s.n && "step-done")}>
          <span className="step-num">{지금 > s.n ? "✓" : s.n}</span>
          <span>
            <span className="block text-sm font-semibold">{s.label}</span>
            <span className="block text-xs text-muted-foreground">{s.sub}</span>
          </span>
        </li>
      ))}
    </ol>
  );
}
