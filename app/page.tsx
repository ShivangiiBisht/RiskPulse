"use client";

import { useState } from "react";
import IngestionPanel from "./components/IngestionPanel";
import RebalancerPanel from "./components/RebalancerPanel";
import SandboxPanel from "./components/SandboxPanel";
import SignalsPanel from "./components/SignalsPanel";
import StressPanel from "./components/StressPanel";
import { RegimeBadge } from "./components/ui";
import { API_URL, useApi, type Rebalance } from "./lib/api";

const TABS = [
  { id: "ingest", label: "1. Ingestion" },
  { id: "signals", label: "2. Risk signals" },
  { id: "rebalance", label: "3. Module A: Rebalancer" },
  { id: "stress", label: "4. Module B: Stress test" },
  { id: "sandbox", label: "Sandbox" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function Home() {
  const [tab, setTab] = useState<TabId>("ingest");
  const health = useApi<{ status: string; offline_mode: boolean }>("/health", 10000);
  const regime = useApi<Rebalance>("/rebalance/current", 10000);

  return (
    <main className="mx-auto w-full max-w-6xl space-y-4 p-6 text-zinc-900 dark:text-zinc-100">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Risk Engine</h1>
          <p className="text-sm text-zinc-500">
            Unstructured text → sentiment, event type, impact → tactical rebalancing + strategic stress testing
          </p>
        </div>
        <div className="flex items-center gap-3 text-sm">
          {regime.data && <span className="flex items-center gap-1">Regime <RegimeBadge regime={regime.data.regime} /></span>}
          <span className="flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${health.data ? "bg-green-500" : health.error ? "bg-red-500" : "bg-zinc-400"}`} />
            {health.data ? "Backend online" : health.error ? `Backend offline (${API_URL})` : "Checking..."}
          </span>
          {health.data?.offline_mode && (
            <span className="rounded bg-amber-100 px-2 py-0.5 text-amber-800">OFFLINE_MODE</span>
          )}
        </div>
      </header>

      <nav className="flex flex-wrap gap-1 border-b border-zinc-200 dark:border-zinc-800">
        {TABS.map((item) => (
          <button
            key={item.id}
            onClick={() => setTab(item.id)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm ${
              tab === item.id ? "border-blue-500 font-semibold" : "border-transparent text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>

      {tab === "ingest" && <IngestionPanel />}
      {tab === "signals" && <SignalsPanel />}
      {tab === "rebalance" && <RebalancerPanel />}
      {tab === "stress" && <StressPanel />}
      {tab === "sandbox" && <SandboxPanel />}
    </main>
  );
}
