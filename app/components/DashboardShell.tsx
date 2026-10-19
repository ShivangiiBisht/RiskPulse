"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useApi, type Rebalance } from "../lib/api";
import Logo from "./Logo";
import { RegimeBadge } from "./ui";

const NAV = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/ingestion", label: "Ingestion" },
  { href: "/dashboard/signals", label: "Risk signals" },
  { href: "/dashboard/rebalancer", label: "Rebalancer" },
  { href: "/dashboard/stress", label: "Stress test" },
  { href: "/dashboard/sandbox", label: "Sandbox" },
];

export default function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const health = useApi<{ status: string; offline_mode: boolean }>("/health", 10000);
  const regime = useApi<Rebalance>("/rebalance/current", 10000);

  const links = NAV.map((item) => {
    const active = item.href === "/dashboard" ? pathname === item.href : pathname.startsWith(item.href);
    return (
      <Link key={item.href} href={item.href} aria-current={active ? "page" : undefined}
            className={`whitespace-nowrap rounded-sm px-3 py-2 text-sm ${active ? "bg-ink font-medium text-white" : "text-muted hover:bg-track hover:text-ink"}`}>
        {item.label}
      </Link>
    );
  });

  return (
    <div className="min-h-screen md:grid md:grid-cols-[220px_1fr]">
      <aside className="border-b border-line bg-surface md:sticky md:top-0 md:h-screen md:border-b-0 md:border-r">
        <div className="flex h-full flex-col gap-4 p-4">
          <Link href="/" aria-label="RiskPulse home"><Logo /></Link>
          <nav className="flex gap-1 overflow-x-auto md:flex-col" aria-label="Dashboard">{links}</nav>
          <div className="mt-auto hidden space-y-2 border-t border-line pt-4 text-xs text-muted md:block">
            <div className="flex items-center justify-between">
              <span>Regime</span>
              {regime.data ? <RegimeBadge regime={regime.data.regime} /> : <span>-</span>}
            </div>
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${health.data ? "bg-pos" : health.error ? "bg-neg" : "bg-line-strong"}`} />
              {health.data ? "Backend online" : health.error ? "Backend offline" : "Checking"}
              {health.data?.offline_mode && <span className="rounded-sm bg-warn/15 px-1.5 text-warn">offline mode</span>}
            </div>
            <Link href="/" className="inline-block hover:text-ink">Back to home</Link>
          </div>
        </div>
      </aside>
      <div className="min-w-0 p-5 md:p-8">{children}</div>
    </div>
  );
}
