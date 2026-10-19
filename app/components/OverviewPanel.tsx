"use client";

import Link from "next/link";
import { useApi, type Rebalance, type Signal, type Stats, type StressResult } from "../lib/api";
import { Card, ErrorNote, ImpactBadge, money, primaryButtonClass, RegimeBadge, SeverityScale, shortTime } from "./ui";

export default function OverviewPanel() {
  const stats = useApi<Stats>("/stats", 5000);
  const rebalance = useApi<Rebalance>("/rebalance/current", 5000);
  const severe = useApi<Signal[]>("/signals?min_impact=7&limit=200", 5000);
  const auto = useApi<{ triggered: boolean; reason?: string; result?: StressResult }>("/stress/auto", 8000);

  const table = rebalance.data?.table ?? [];
  const over = [...table].sort((a, b) => b.delta - a.delta).slice(0, 3);
  const under = [...table].sort((a, b) => a.delta - b.delta).slice(0, 3);
  const empty = stats.data !== null && stats.data.signals === 0;

  return (
    <div className="space-y-5">
      <ErrorNote message={stats.error} />
      {empty && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-line bg-surface p-5">
          <div>
            <div className="font-serif text-xl">No signals yet</div>
            <p className="text-sm text-muted">Ingest data to score it, or skip straight to a crisis scenario.</p>
          </div>
          <div className="flex gap-2">
            <Link href="/dashboard/ingestion" className={primaryButtonClass}>Ingest data</Link>
            <Link href="/dashboard/sandbox" className="rounded-sm border border-line-strong bg-surface px-4 py-2 text-sm font-medium hover:bg-surface-2">Open sandbox</Link>
          </div>
        </div>
      )}

      <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr_1fr]">
        <Card title="Risk regime">
          <div className="flex items-center gap-3">
            {rebalance.data ? <RegimeBadge regime={rebalance.data.regime} /> : <span className="text-muted">-</span>}
            <span className="text-sm text-muted">stress index {rebalance.data?.stress_index.toFixed(2) ?? "-"}</span>
          </div>
          <div className="mt-4"><SeverityScale compact marker={(rebalance.data?.stress_index ?? 0) * 10} /></div>
          <p className="mt-2 text-xs text-muted">Elevated from 0.25, crisis from 0.55.</p>
        </Card>
        <Card title="Signals scored">
          <div className="font-serif text-4xl tabular-nums">{stats.data?.signals ?? "-"}</div>
          <p className="mt-1 text-sm text-muted">from {stats.data?.total ?? "-"} documents</p>
        </Card>
        <Card title="High-impact events">
          <div className="font-serif text-4xl tabular-nums">{severe.data?.length ?? "-"}</div>
          <p className="mt-1 text-sm text-muted">impact 7 or more</p>
        </Card>
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr]">
        <Card title="Latest high-impact events" right={<Link href="/dashboard/signals" className="text-sm text-cobalt hover:underline">All signals</Link>}>
          {(severe.data ?? []).length === 0 && <p className="text-sm text-muted">Nothing at impact 7 or above yet.</p>}
          <ul className="divide-y divide-line">
            {(severe.data ?? []).slice(0, 6).map((s) => (
              <li key={s.signal_id} className="flex items-start gap-3 py-2.5 text-sm">
                <ImpactBadge impact={s.impact} />
                <div className="min-w-0">
                  <div className="text-xs text-muted">{s.entity} · {s.event_type} · {shortTime(s.timestamp)}</div>
                  <div>{s.text_snippet}</div>
                </div>
              </li>
            ))}
          </ul>
        </Card>

        <div className="space-y-5">
          <Card title="Index tilt" right={<Link href="/dashboard/rebalancer" className="text-sm text-cobalt hover:underline">Rebalancer</Link>}>
            <TiltList heading="Overweight" rows={over} />
            <div className="my-3 border-t border-line" />
            <TiltList heading="Underweight" rows={under} />
          </Card>
          <Card title="Portfolio stress" right={<Link href="/dashboard/stress" className="text-sm text-cobalt hover:underline">Stress test</Link>}>
            {auto.data?.triggered && auto.data.result ? (
              <div className="text-sm">
                <div className="font-serif text-3xl text-crisis tabular-nums">{auto.data.result.pnl_pct}%</div>
                <div className="text-muted">{auto.data.result.event_type}, impact {auto.data.result.impact}, book value {money(auto.data.result.before)} to {money(auto.data.result.after)}</div>
              </div>
            ) : (
              <p className="text-sm text-muted">{auto.data?.reason ?? "Loading"}</p>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

function TiltList({ heading, rows }: { heading: string; rows: Rebalance["table"] }) {
  return (
    <div>
      <div className="mb-1 text-xs text-muted">{heading}</div>
      {rows.length === 0 && <div className="text-sm text-muted">-</div>}
      {rows.map((row) => (
        <div key={row.ticker} className="flex justify-between text-sm">
          <span className="font-medium">{row.ticker}</span>
          <span className={`tabular-nums ${row.delta >= 0 ? "text-pos" : "text-neg"}`}>
            {row.delta >= 0 ? "+" : ""}{(row.delta * 100).toFixed(2)} pp
          </span>
        </div>
      ))}
    </div>
  );
}
