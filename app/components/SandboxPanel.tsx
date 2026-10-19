"use client";

import { useState } from "react";
import { api, useApi, type SandboxReport, type Scenario } from "../lib/api";
import { buttonClass, Card, ErrorNote, ImpactBadge, pct, RegimeBadge, SentimentCell } from "./ui";
import { StressResultView } from "./StressPanel";

export default function SandboxPanel() {
  const scenarios = useApi<Scenario[]>("/sandbox/scenarios");
  const [text, setText] = useState("Regulators open antitrust probe into Apple, fine possible");
  const [report, setReport] = useState<SandboxReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function call<T>(path: string, body?: unknown): Promise<T | null> {
    setBusy(true);
    try {
      const result = await api<T>(path, {
        method: "POST",
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      });
      setError(null);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
      return null;
    } finally {
      setBusy(false);
    }
  }

  async function inject(path: string, body?: unknown) {
    const result = await call<SandboxReport>(path, body);
    if (result) {
      setReport(result);
      setMessage(null);
    }
  }

  async function reset() {
    const result = await call<{ signals_deleted: number; documents_deleted: number }>("/sandbox/reset");
    if (result) {
      setReport(null);
      setMessage(`Sandbox cleared (${result.documents_deleted} headlines removed). Real data untouched.`);
    }
  }

  return (
    <div className="space-y-4">
      <ErrorNote message={error} />
      <Card title="What-if sandbox: inject a headline and watch the engine react">
        <textarea className="w-full rounded border border-zinc-300 bg-transparent p-2 text-sm dark:border-zinc-700"
                  rows={2} value={text} onChange={(e) => setText(e.target.value)} />
        <div className="mt-2 flex flex-wrap gap-2">
          <button className={buttonClass} disabled={busy} onClick={() => inject("/sandbox/headline", { text })}>
            Inject headline
          </button>
          <button className={buttonClass} disabled={busy} onClick={reset}>Reset sandbox</button>
        </div>
        <div className="mt-4 text-sm font-medium">Crisis replay scenarios (synthetic, modelled on historic episodes)</div>
        <div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {(scenarios.data ?? []).map((s) => (
            <button key={s.id} disabled={busy} onClick={() => inject(`/sandbox/scenario/${s.id}`)}
                    className="rounded border border-zinc-300 p-3 text-left text-sm hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800">
              <div className="font-medium">{s.name}</div>
              <div className="text-xs text-zinc-500">{s.description}</div>
              <div className="mt-1 text-xs text-zinc-400">{s.headlines.length} headlines</div>
            </button>
          ))}
        </div>
        {message && <p className="mt-3 text-sm text-zinc-500">{message}</p>}
      </Card>

      {report && (
        <>
          <Card title={report.scenario ? `Result: ${report.scenario.name}` : "Result"}>
            <div className="mb-3 flex flex-wrap items-center gap-3 text-sm">
              Risk regime <RegimeBadge regime={report.regime_before} /> → <RegimeBadge regime={report.regime_after} />
              <span className="text-zinc-500">
                stress index {report.stress_index_before.toFixed(2)} → {report.stress_index_after.toFixed(2)}
              </span>
            </div>
            <table className="mb-4 w-full text-left text-sm">
              <thead className="text-zinc-500">
                <tr><th className="py-1 pr-3">Entity</th><th className="pr-3">Sentiment</th><th className="pr-3">Event</th><th className="pr-3">Impact</th><th>Headline</th></tr>
              </thead>
              <tbody>
                {report.signals.map((s) => (
                  <tr key={s.signal_id} className="border-t border-zinc-200 dark:border-zinc-800">
                    <td className="py-1.5 pr-3 font-medium">{s.entity}</td>
                    <td className="pr-3"><SentimentCell value={s.sentiment} /></td>
                    <td className="pr-3">{s.event_type}</td>
                    <td className="pr-3"><ImpactBadge impact={s.impact} /></td>
                    <td>{s.text_snippet}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mb-1 text-sm font-medium">Largest weight changes (index rebalanced)</div>
            <div className="grid gap-1 text-sm sm:grid-cols-2">
              {report.weight_changes.map((c) => (
                <div key={c.ticker} className="flex justify-between border-b border-zinc-200 py-1 dark:border-zinc-800">
                  <span className="font-medium">{c.ticker}</span>
                  <span className="tabular-nums">
                    {pct(c.before)} → {pct(c.after)}{" "}
                    <span className={c.delta >= 0 ? "text-green-600" : "text-red-600"}>
                      ({c.delta >= 0 ? "+" : ""}{(c.delta * 100).toFixed(2)} pp)
                    </span>
                  </span>
                </div>
              ))}
            </div>
            <p className="mt-2 text-xs text-zinc-500">See the Rebalancer tab for the full weight history and contagion detail.</p>
          </Card>

          {report.stress_test ? (
            <Card title="Stress test triggered automatically (impact ≥ 7)">
              <StressResultView result={report.stress_test} />
            </Card>
          ) : (
            <p className="text-sm text-zinc-500">No signal reached impact ≥ 7, so no stress test was triggered.</p>
          )}
        </>
      )}
    </div>
  );
}
