"use client";

import { Fragment, useState } from "react";
import { useApi, type Signal } from "../lib/api";
import { Card, ErrorNote, ImpactBadge, selectClass, SentimentCell, shortTime } from "./ui";

export default function SignalsPanel() {
  const [ticker, setTicker] = useState("");
  const [eventType, setEventType] = useState("");
  const [minImpact, setMinImpact] = useState(1);
  const [open, setOpen] = useState<number | null>(null);

  const tickers = useApi<Record<string, unknown>>("/tickers");
  const eventTypes = useApi<string[]>("/event-types");
  const query = new URLSearchParams({ limit: "100", min_impact: String(minImpact) });
  if (ticker) query.set("ticker", ticker);
  if (eventType) query.set("event_type", eventType);
  const signals = useApi<Signal[]>(`/signals?${query.toString()}`, 5000);

  return (
    <div className="space-y-4">
      <ErrorNote message={signals.error} />
      <Card
        title="Structured risk signals (the Risk Engine output)"
        right={
          <div className="flex flex-wrap gap-2">
            <select className={selectClass} value={ticker} onChange={(e) => setTicker(e.target.value)}>
              <option value="">All entities</option>
              <option value="MARKET">MARKET (macro)</option>
              {Object.keys(tickers.data ?? {}).map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <select className={selectClass} value={eventType} onChange={(e) => setEventType(e.target.value)}>
              <option value="">All events</option>
              {(eventTypes.data ?? []).map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <select className={selectClass} value={minImpact} onChange={(e) => setMinImpact(Number(e.target.value))}>
              {[1, 3, 5, 7, 9].map((n) => <option key={n} value={n}>impact ≥ {n}</option>)}
            </select>
          </div>
        }
      >
        <p className="mb-3 text-xs text-zinc-500">
          Each row: entity, sentiment [-1, 1], event class, impact [1-10]. Click a row to see why the impact score is what it is.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-zinc-500">
              <tr>
                <th className="py-1 pr-3">Time</th><th className="pr-3">Entity</th><th className="pr-3">Sentiment</th>
                <th className="pr-3">Event</th><th className="pr-3">Impact</th><th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {(signals.data ?? []).length === 0 && (
                <tr><td colSpan={6} className="py-4 text-center text-zinc-500">No signals yet. Ingest data first.</td></tr>
              )}
              {(signals.data ?? []).map((s) => (
                <Fragment key={s.signal_id}>
                  <tr className="cursor-pointer border-t border-zinc-200 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
                      onClick={() => setOpen(open === s.signal_id ? null : s.signal_id)}>
                    <td className="whitespace-nowrap py-1.5 pr-3 text-zinc-500">{shortTime(s.timestamp)}</td>
                    <td className="pr-3 font-medium">{s.entity}</td>
                    <td className="pr-3"><SentimentCell value={s.sentiment} /></td>
                    <td className="pr-3">{s.event_type}</td>
                    <td className="pr-3"><ImpactBadge impact={s.impact} /></td>
                    <td>{s.text_snippet}</td>
                  </tr>
                  {open === s.signal_id && (
                    <tr className="bg-zinc-50 text-xs dark:bg-zinc-900">
                      <td colSpan={6} className="px-3 py-2">
                        impact = 1 + 9 × severity {s.breakdown.severity} × magnitude {s.breakdown.magnitude} × credibility{" "}
                        {s.breakdown.credibility} × corroboration {s.breakdown.corroboration_boost} (n={s.breakdown.corroboration})
                        {" "}= raw {s.breakdown.raw} → {s.impact}. Source: {s.provider}, confidence {s.confidence}, models: {s.backend}.
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
