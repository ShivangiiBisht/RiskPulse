"use client";

import { useState } from "react";
import { api, useApi, type StressResult } from "../lib/api";
import { buttonClass, Card, ErrorNote, ImpactBadge, money, selectClass } from "./ui";

export function StressResultView({ result }: { result: StressResult }) {
  const maxLoss = Math.max(1, ...result.by_asset_class.map((c) => Math.abs(c.pnl)));
  return (
    <div className="space-y-4 text-sm">
      <div className="flex flex-wrap items-center gap-3">
        <span className="font-semibold">{result.event_type}</span>
        <ImpactBadge impact={result.impact} />
        <span className="text-zinc-500">shock scale ×{result.scale}</span>
        {result.tickers.length > 0 && <span className="text-zinc-500">linked: {result.tickers.join(", ")}</span>}
      </div>
      {result.headline && <p className="italic text-zinc-600 dark:text-zinc-400">Triggered by: {result.headline}</p>}

      <div className="grid gap-3 sm:grid-cols-3">
        <Big label="Portfolio value before" value={money(result.before)} />
        <Big label="After stress" value={money(result.after)} />
        <Big label="P&L" value={`${money(result.pnl)} (${result.pnl_pct}%)`} negative={result.pnl < 0} />
      </div>

      <div className="space-y-2">
        {result.by_asset_class.map((c) => (
          <div key={c.asset_class} className="grid grid-cols-[90px_1fr_190px] items-center gap-3">
            <span className="capitalize">{c.asset_class}</span>
            <div className="h-3 rounded bg-zinc-200 dark:bg-zinc-800">
              <div className="h-3 rounded bg-red-500" style={{ width: `${(Math.abs(c.pnl) / maxLoss) * 100}%` }} />
            </div>
            <span className="tabular-nums text-xs">
              {money(c.before)} → {money(c.after)} ({c.pnl_pct}%)
            </span>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div>
          <div className="mb-1 font-medium">Top losing positions</div>
          <table className="w-full text-left text-xs">
            <tbody>
              {result.top_losers.slice(0, 6).map((row) => (
                <tr key={row.asset_id} className="border-t border-zinc-200 dark:border-zinc-800">
                  <td className="py-1">{row.asset_id}</td>
                  <td>{row.ticker || "-"}{row.linked_to_event && " ●"}</td>
                  <td className="text-zinc-500">{row.counterparty}</td>
                  <td className="text-right tabular-nums text-red-600">{money(row.pnl)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-1 text-xs text-zinc-500">● = asset linked to a company named in the event (1.5× idiosyncratic shock)</p>
        </div>
        <div>
          <div className="mb-1 font-medium">Shocks applied</div>
          <ul className="text-xs text-zinc-600 dark:text-zinc-400">
            <li>Equity: {(result.shocks.equity_shock * 100).toFixed(0)}% × scale × beta</li>
            <li>Rates: {result.shocks.rate_shift_bp >= 0 ? "+" : ""}{result.shocks.rate_shift_bp} bp × scale</li>
            <li>Credit spreads: +{result.shocks.spread_shift_bp} bp × scale × rating multiplier</li>
            <li className="mt-1">{result.shocks.rationale}</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

function Big({ label, value, negative }: { label: string; value: string; negative?: boolean }) {
  return (
    <div className="rounded border border-zinc-200 p-3 dark:border-zinc-800">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className={`text-lg font-semibold ${negative ? "text-red-600" : ""}`}>{value}</div>
    </div>
  );
}

const EVENT_OPTIONS = ["Geopolitical", "Macroeconomic", "Credit Event", "Regulatory", "Merger/Acquisition", "Earnings", "Product Launch", "Other"];

export default function StressPanel() {
  const auto = useApi<{ triggered: boolean; reason?: string; result?: StressResult }>("/stress/auto", 8000);
  const [eventType, setEventType] = useState("Geopolitical");
  const [impact, setImpact] = useState(8);
  const [tickers, setTickers] = useState("");
  const [manual, setManual] = useState<StressResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function runManual() {
    try {
      const result = await api<StressResult>("/stress/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_type: eventType,
          impact,
          tickers: tickers.split(",").map((t) => t.trim().toUpperCase()).filter(Boolean),
        }),
      });
      setManual(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    }
  }

  return (
    <div className="space-y-4">
      <ErrorNote message={auto.error ?? error} />
      <Card title="Module B: event-triggered stress test (automatic)">
        {auto.data?.triggered && auto.data.result ? (
          <StressResultView result={auto.data.result} />
        ) : (
          <p className="text-sm text-zinc-500">
            {auto.data?.reason ?? "Loading..."} A stress test fires automatically when the engine detects an event with
            impact ≥ 7. Try a scenario in the Sandbox tab.
          </p>
        )}
      </Card>

      <Card title="Manual stress test">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <select className={selectClass} value={eventType} onChange={(e) => setEventType(e.target.value)}>
            {EVENT_OPTIONS.map((o) => <option key={o}>{o}</option>)}
          </select>
          <label className="flex items-center gap-2 text-sm">
            impact {impact}
            <input type="range" min={1} max={10} value={impact} onChange={(e) => setImpact(Number(e.target.value))} />
          </label>
          <input className={`${selectClass} w-48`} placeholder="linked tickers, e.g. JPM,GS" value={tickers}
                 onChange={(e) => setTickers(e.target.value)} />
          <button className={buttonClass} onClick={runManual}>Run stress test</button>
        </div>
        {manual && <StressResultView result={manual} />}
      </Card>
    </div>
  );
}
