"use client";

import { Fragment, useState } from "react";
import { useApi, type Rebalance, type Timeline } from "../lib/api";
import StackedArea, { tickerColor } from "./StackedArea";
import { Card, ErrorNote, ImpactBadge, pct, RegimeBadge, SentimentCell, shortTime } from "./ui";

export default function RebalancerPanel() {
  const current = useApi<Rebalance>("/rebalance/current", 5000);
  const timeline = useApi<Timeline>("/rebalance/timeline?max_points=60", 5000);
  const [open, setOpen] = useState<string | null>(null);
  const snapshot = current.data;

  return (
    <div className="space-y-4">
      <ErrorNote message={current.error ?? timeline.error} />
      <Card
        title="Module A: tactical index rebalancer"
        right={snapshot && <RegimeBadge regime={snapshot.regime} />}
      >
        {snapshot && (
          <div className="mb-3 grid gap-3 text-sm sm:grid-cols-4">
            <Info label="As of" value={snapshot.as_of ? shortTime(snapshot.as_of) : "-"} />
            <Info label="Stress index" value={snapshot.stress_index.toFixed(2)} />
            <Info label="Market sentiment" value={snapshot.market_sentiment.toFixed(2)} />
            <Info label="Last turnover" value={pct(snapshot.turnover)} />
          </div>
        )}
        {timeline.data && <StackedArea timeline={timeline.data} />}
        <p className="mt-2 text-xs text-zinc-500">
          Weights over time (event-driven rebalances, replayed in timestamp order). Lower strip: stress index with the
          ELEVATED (0.25) and CRISIS (0.55) thresholds.
        </p>
      </Card>

      <Card title="Current weights and why">
        <p className="mb-3 text-xs text-zinc-500">
          Effective sentiment = own sentiment + contagion from shocked sector peers + beta-scaled market effect. Click a
          row to see the headlines driving it.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-zinc-500">
              <tr>
                <th className="py-1 pr-3">Ticker</th><th className="pr-3">Sector</th><th className="pr-3">Weight</th>
                <th className="pr-3">vs equal</th><th className="pr-3">Own</th><th className="pr-3">Contagion</th>
                <th className="pr-3">Market</th><th>Effective</th>
              </tr>
            </thead>
            <tbody>
              {(snapshot?.table ?? []).map((row) => (
                <Fragment key={row.ticker}>
                  <tr className="cursor-pointer border-t border-zinc-200 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
                      onClick={() => setOpen(open === row.ticker ? null : row.ticker)}>
                    <td className="py-1.5 pr-3 font-medium">
                      <span className="mr-1.5 inline-block h-2.5 w-2.5 rounded-sm"
                            style={{ background: tickerColor(timeline.data?.tickers ?? [], row.ticker) }} />
                      {row.ticker}
                    </td>
                    <td className="pr-3 text-zinc-500">{row.sector}</td>
                    <td className="pr-3">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-24 rounded bg-zinc-200 dark:bg-zinc-800">
                          <div className="h-2 rounded bg-blue-500" style={{ width: `${Math.min(100, row.weight * 600)}%` }} />
                        </div>
                        <span className="tabular-nums">{pct(row.weight)}</span>
                      </div>
                    </td>
                    <td className={`pr-3 tabular-nums ${row.delta >= 0 ? "text-green-600" : "text-red-600"}`}>
                      {row.delta >= 0 ? "+" : ""}{(row.delta * 100).toFixed(2)} pp
                    </td>
                    <td className="pr-3 tabular-nums">{row.own_sentiment.toFixed(2)}</td>
                    <td className="pr-3 tabular-nums" title={row.contagion_from.length ? `from ${row.contagion_from.join(", ")}` : ""}>
                      {row.contagion.toFixed(2)}
                    </td>
                    <td className="pr-3 tabular-nums">{row.market_effect.toFixed(2)}</td>
                    <td><SentimentCell value={row.effective_sentiment} /></td>
                  </tr>
                  {open === row.ticker && (
                    <tr className="bg-zinc-50 text-xs dark:bg-zinc-900">
                      <td colSpan={8} className="space-y-1 px-3 py-2">
                        {row.contagion_from.length > 0 && (
                          <div>Contagion from shocked peers: <b>{row.contagion_from.join(", ")}</b></div>
                        )}
                        {row.drivers.length === 0 && <div>No direct signals for this ticker.</div>}
                        {row.drivers.map((driver, index) => (
                          <div key={index} className="flex items-center gap-2">
                            <ImpactBadge impact={driver.impact} />
                            <span className="tabular-nums">{driver.sentiment >= 0 ? "+" : ""}{driver.sentiment.toFixed(2)}</span>
                            <span className="text-zinc-500">{driver.event_type}</span>
                            <span>{driver.text}</span>
                          </div>
                        ))}
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-zinc-500">{label}</div>
      <div className="font-semibold">{value}</div>
    </div>
  );
}
