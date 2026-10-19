import { useCallback, useEffect, useState } from "react";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init);
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      /* keep status text */
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

/** GET helper: loads on mount / path change, optionally polls, and exposes reload(). */
export function useApi<T>(path: string | null, intervalMs = 0) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  const reload = useCallback(() => setVersion((v) => v + 1), []);

  useEffect(() => {
    if (path === null) return;
    let cancelled = false;
    const load = () =>
      api<T>(path)
        .then((result) => {
          if (cancelled) return;
          setData(result);
          setError(null);
        })
        .catch((err: unknown) => {
          if (!cancelled) setError(err instanceof Error ? err.message : "Request failed");
        });
    load();
    const timer = intervalMs > 0 ? setInterval(load, intervalMs) : undefined;
    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [path, intervalMs, version]);

  return { data, error, reload };
}

export type Doc = {
  doc_id: string; source: string; provider: string; published_at: string; text: string;
  url: string | null; author: string | null; tickers: string[]; scored: boolean;
};

export type Stats = {
  total: number; by_provider: Record<string, number>; unscored: number; without_ticker: number;
  signals: number; signals_by_event: Record<string, number>;
};

export type Job = {
  status: "queued" | "running" | "done" | "failed";
  stats?: {
    seen?: number; inserted?: number; duplicates?: number; too_short?: number; without_ticker?: number;
    scoring?: { documents: number; signals: number; sentiment_backend: string | null; event_backend: string | null };
  };
  error?: string;
};

export type Signal = {
  signal_id: number; doc_id: string; entity: string; timestamp: string; provider: string;
  sentiment: number; event_type: string; event_confidence: number; impact: number;
  confidence: number; credibility: number; text_snippet: string; url: string | null;
  breakdown: Record<string, number>; backend: string;
};

export type Driver = { text: string; sentiment: number; impact: number; event_type: string; provider: string };

export type WeightRow = {
  ticker: string; sector: string; base_weight: number; weight: number; delta: number;
  own_sentiment: number; contagion: number; contagion_from: string[]; market_effect: number;
  effective_sentiment: number; n_signals: number; drivers: Driver[];
};

export type Rebalance = {
  as_of: string | null; stress_index: number; regime: string; turnover: number;
  market_sentiment: number; weights: Record<string, number>; table: WeightRow[];
};

export type Timeline = {
  tickers: string[];
  points: { timestamp: string; weights: Record<string, number>; stress_index: number; regime: string }[];
};

export type StressResult = {
  event_type: string; impact: number; scale: number; tickers: string[]; headline: string | null;
  shocks: { equity_shock: number; rate_shift_bp: number; spread_shift_bp: number; rationale: string };
  before: number; after: number; pnl: number; pnl_pct: number; assets: number;
  by_asset_class: { asset_class: string; before: number; pnl: number; after: number; pnl_pct: number }[];
  top_losers: { asset_id: string; asset_type: string; counterparty: string; ticker: string; pnl: number; linked_to_event: boolean }[];
  supporting_signals?: number;
};

export type SandboxReport = {
  signals: Signal[]; regime_before: string; regime_after: string;
  stress_index_before: number; stress_index_after: number;
  weight_changes: { ticker: string; before: number; after: number; delta: number }[];
  stress_test: StressResult | null; scenario?: { id: string; name: string };
};

export type Scenario = { id: string; name: string; description: string; headlines: { text: string; minutes: number }[] };
