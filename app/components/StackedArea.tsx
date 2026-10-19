import { shortTime } from "./ui";
import type { Timeline } from "../lib/api";

const W = 800, H = 260, LEFT = 40, TOP = 8, BOTTOM = 22;
const color = (index: number) => `hsl(${(index * 137.5) % 360} 62% 52%)`;

export function tickerColor(tickers: string[], ticker: string) {
  return color(tickers.indexOf(ticker));
}

export default function StackedArea({ timeline }: { timeline: Timeline }) {
  const { points, tickers } = timeline;
  if (points.length < 2) {
    return <p className="text-sm text-zinc-500">Need at least two rebalance points. Ingest data or run a sandbox scenario.</p>;
  }
  const plotW = W - LEFT - 8, plotH = H - TOP - BOTTOM;
  const x = (i: number) => LEFT + (i / (points.length - 1)) * plotW;
  const y = (share: number) => TOP + (1 - share) * plotH;

  const cumulative = points.map((point) => {
    let running = 0;
    return tickers.map((t) => (running += point.weights[t] ?? 0));
  });
  const areas = tickers.map((t, k) => {
    const upper = points.map((_, i) => `${x(i).toFixed(1)},${y(cumulative[i][k]).toFixed(1)}`);
    const lower = points.map((_, i) => `${x(i).toFixed(1)},${y(k === 0 ? 0 : cumulative[i][k - 1]).toFixed(1)}`).reverse();
    return { t, d: `M${upper.join(" L")} L${lower.join(" L")} Z` };
  });

  const stressY = (value: number) => 36 - value * 32;
  const stressPath = points.map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${stressY(p.stress_index).toFixed(1)}`).join(" ");

  return (
    <div className="space-y-2">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Index weights over time">
        {[0, 0.25, 0.5, 0.75, 1].map((tick) => (
          <g key={tick}>
            <line x1={LEFT} x2={W - 8} y1={y(tick)} y2={y(tick)} stroke="currentColor" opacity={0.12} />
            <text x={LEFT - 6} y={y(tick) + 3} textAnchor="end" fontSize={10} fill="currentColor" opacity={0.6}>
              {Math.round(tick * 100)}%
            </text>
          </g>
        ))}
        {areas.map((area) => (
          <path key={area.t} d={area.d} fill={tickerColor(tickers, area.t)} opacity={0.85} stroke="white" strokeWidth={0.4}>
            <title>{area.t}</title>
          </path>
        ))}
        <text x={LEFT} y={H - 6} fontSize={10} fill="currentColor" opacity={0.6}>{shortTime(points[0].timestamp)}</text>
        <text x={W - 8} y={H - 6} fontSize={10} textAnchor="end" fill="currentColor" opacity={0.6}>
          {shortTime(points[points.length - 1].timestamp)}
        </text>
      </svg>

      <svg viewBox={`0 0 ${W} 44`} className="w-full" role="img" aria-label="Stress index over time">
        <text x={LEFT - 6} y={14} textAnchor="end" fontSize={10} fill="currentColor" opacity={0.6}>stress</text>
        {[0.25, 0.55].map((level) => (
          <line key={level} x1={LEFT} x2={W - 8} y1={stressY(level)} y2={stressY(level)} stroke={level > 0.5 ? "#dc2626" : "#d97706"} strokeDasharray="3 3" opacity={0.6} />
        ))}
        <path d={stressPath} fill="none" stroke="currentColor" strokeWidth={1.5} />
      </svg>

      <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs">
        {tickers.map((t) => (
          <span key={t} className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: tickerColor(tickers, t) }} />{t}
          </span>
        ))}
      </div>
    </div>
  );
}
