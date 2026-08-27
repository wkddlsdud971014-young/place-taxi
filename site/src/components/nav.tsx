"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const 탭 = [
  { href: "/", label: "웹 서비스", desc: "칸을 채운다" },
  { href: "/bot", label: "Gradio 봇", desc: "말로 한다" },
];

export function Nav() {
  const path = usePathname();
  return (
    <header className="border-b bg-background">
      <div className="mx-auto flex max-w-6xl items-end justify-between gap-6 px-6 pt-6">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            식당 예약하고 택시 부르기
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            같은 일을 두 가지 방식으로. 창고는 하나를 같이 씁니다.
          </p>
        </div>
      </div>
      <nav className="mx-auto flex max-w-6xl gap-6 px-6">
        {탭.map((t) => (
          <Link
            key={t.href}
            href={t.href}
            className={cn(
              "-mb-px border-b-2 py-3 text-sm font-medium transition-colors",
              path === t.href
                ? "border-foreground text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            {t.label}
            <span className="ml-2 text-xs font-normal text-muted-foreground">
              {t.desc}
            </span>
          </Link>
        ))}
      </nav>
    </header>
  );
}
