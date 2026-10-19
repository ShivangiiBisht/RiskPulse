import type { ReactNode } from "react";

/** The product's signature: a 1-10 severity scale, teal (calm) to crimson (systemic). */
export const SEVERITY = [
  "#2a9d8f", "#4ba58a", "#78ad7e", "#a6b26c", "#d3b24f",
  "#e6a23c", "#ee8434", "#e5602f", "#cc3a2f", "#9e1f45",
];
export const sevColor = (n: number) => SEVERITY[Math.max(1, Math.min(10, Math.round(n))) - 1];
const darkText = (n: number) => n >= 4 && n <= 7;

export function SeverityScale({ marker, threshold, compact }: { marker?: number; threshold?: number; compact?: boolean }) {
  return (
    <div>
      <div className="relative flex gap-px">
        {SEVERITY.map((color, index) => {
          const n = index + 1;
          return (
            <div key={n} className={`flex flex-1 items-center justify-center text-xs font-medium ${compact ? "h-2" : "h-8"}`}
                 style={{ background: color, color: darkText(n) ? "#0f1b33" : "#fff" }}>
              {!compact && n}
            </div>
          );
        })}
        {marker !== undefined && (
          <div className="absolute -top-1.5 h-[calc(100%+12px)] w-0.5 bg-ink" style={{ left: `${Math.min(100, Math.max(0, marker * 10))}%` }} />
        )}
      </div>
      {threshold !== undefined && !compact && (
        <div className="relative mt-1 h-4 text-xs text-muted">
          <span className="absolute -translate-x-1/2" style={{ left: `${(threshold - 1) * 10}%` }}>
            ▲ stress test fires from {threshold}
          </span>
        </div>
      )}
    </div>
  );
}

const REGIME_STYLE: Record<string, string> = {
  NORMAL: "bg-pos/10 text-pos",
  ELEVATED: "bg-warn/15 text-warn",
  CRISIS: "bg-crisis/10 text-crisis",
};

export function RegimeBadge({ regime }: { regime: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${REGIME_STYLE[regime] ?? "bg-track text-muted"}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {regime}
    </span>
  );
}

export function ImpactBadge({ impact }: { impact: number }) {
  return (
    <span className="inline-block min-w-6 rounded-sm px-1.5 py-0.5 text-center text-xs font-semibold tabular-nums"
          style={{ background: sevColor(impact), color: darkText(impact) ? "#0f1b33" : "#fff" }}>
      {impact}
    </span>
  );
}

export function SentimentCell({ value }: { value: number }) {
  const width = Math.round(Math.abs(value) * 50);
  return (
    <div className="flex items-center gap-2">
      <div className="relative h-1.5 w-24 rounded-full bg-track">
        <div className="absolute left-1/2 top-0 h-1.5 w-px bg-line-strong" />
        <div className={`absolute top-0 h-1.5 rounded-full ${value >= 0 ? "bg-pos" : "bg-neg"}`}
             style={value >= 0 ? { left: "50%", width: `${width}%` } : { right: "50%", width: `${width}%` }} />
      </div>
      <span className="w-12 text-xs tabular-nums">{value >= 0 ? "+" : ""}{value.toFixed(2)}</span>
    </div>
  );
}

export function Card({ title, children, right }: { title?: string; children: ReactNode; right?: ReactNode }) {
  return (
    <section className="rounded-md border border-line bg-surface p-5">
      {(title || right) && (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-serif text-xl">{title}</h2>
          {right}
        </div>
      )}
      {children}
    </section>
  );
}

export function PageHeader({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-6 max-w-3xl">
      <h1 className="font-serif text-3xl">{title}</h1>
      <p className="mt-1 text-muted">{description}</p>
    </div>
  );
}

export function ErrorNote({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div className="rounded-md border border-neg/30 bg-neg/5 p-3 text-sm text-neg">
      {message}. Check that the backend is running (uvicorn app.main:app --reload in backend/).
    </div>
  );
}

export const buttonClass =
  "rounded-sm border border-line-strong bg-surface px-3 py-1.5 text-sm font-medium hover:bg-surface-2 disabled:opacity-50";
export const primaryButtonClass =
  "rounded-sm bg-ink px-4 py-2 text-sm font-medium text-white hover:bg-ink/90 disabled:opacity-50";
export const selectClass = "rounded-sm border border-line-strong bg-surface px-2 py-1 text-sm";

export const shortTime = (iso: string) => iso.replace("T", " ").slice(0, 16);
export const pct = (value: number, digits = 1) => `${(value * 100).toFixed(digits)}%`;
export const money = (value: number) =>
  `${value < 0 ? "-" : ""}$${Math.abs(value).toLocaleString(undefined, { maximumFractionDigits: 1 })}M`;
