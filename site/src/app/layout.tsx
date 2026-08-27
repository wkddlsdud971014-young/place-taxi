import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/nav";

export const metadata: Metadata = {
  title: "장소 + 택시",
  description: "장소를 예약하면 택시 도착지가 저절로 채워집니다",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-muted/40 antialiased">
        <Nav />
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
        <footer className="mx-auto max-w-6xl px-6 pb-10 text-xs text-muted-foreground">
          <a href="/admin" className="hover:underline">🔧 관리자</a>
          <span className="mx-2">·</span>
          <a href="/flow.html" className="hover:underline">🖍️ Flow 밑그림</a>
        </footer>
      </body>
    </html>
  );
}
