import type { ReactNode } from "react";

const REGIME_STYLE: Record<string, string> = {
  NORMAL: "bg-green-100 text-green-800",
  ELEVATED: "bg-amber-100 text-amber-800",
  CRISIS: "bg-red-100 text-red-800",
};

export function RegimeBadge({ regime }: { regime: string }) {
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-semibold ${REGIME_STYLE[regime] ?? "bg-zinc-100 text-zinc-700"}`}>
      {regime}
    </span>
  );
}

export function ImpactBadge({ impact }: { impact: number }) {
  const style =
    impact >= 8 ? "bg-red-600 text-white" : impact >= 6 ? "bg-amber-500 text-white" : "bg-zinc-200 text-zinc-700";
  return <span className={`rounded px-1.5 py-0.5 text-xs font-semibold ${style}`}>{impact}</span>;
}

export function SentimentCell({ value }: { value: number }) {
  const width = Math.round(Math.abs(value) * 50);
  return (
    <div className="flex items-center gap-2">
      <div className="relative h-2 w-24 rounded bg-zinc-200 dark:bg-zinc-800">
        <div className="absolute left-1/2 top-0 h-2 w-px bg-zinc-400" />
        <div
          className={`absolute top-0 h-2 rounded ${value >= 0 ? "bg-green-500" : "bg-red-500"}`}
          style={value >= 0 ? { left: "50%", width: `${width}%` } : { right: "50%", width: `${width}%` }}
        />
      </div>
      <span className="w-12 text-xs tabular-nums">{value >= 0 ? "+" : ""}{value.toFixed(2)}</span>
    </div>
  );
}

export function Card({ title, children, right }: { title?: string; children: ReactNode; right?: ReactNode }) {
  return (
    <section className="rounded border border-zinc-200 p-4 dark:border-zinc-800">
      {(title || right) && (
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="font-medium">{title}</h2>
          {right}
        </div>
      )}
      {children}
    </section>
  );
}

export function ErrorNote({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">
      {message}. Is the backend running?
    </div>
  );
}

export const buttonClass =
  "rounded border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800";
export const selectClass =
  "rounded border border-zinc-300 bg-transparent px-2 py-1 text-sm dark:border-zinc-700";

export const shortTime = (iso: string) => iso.replace("T", " ").slice(0, 16);
export const pct = (value: number, digits = 1) => `${(value * 100).toFixed(digits)}%`;
export const money = (value: number) =>
  `${value < 0 ? "-" : ""}$${Math.abs(value).toLocaleString(undefined, { maximumFractionDigits: 1 })}M`;
