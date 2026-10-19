import { SEVERITY } from "../ui";

// Illustration only: sector weights drifting toward defensives as the regime moves into stress.
const SERIES = [
  { name: "Financials", color: "#2447f5", values: [28, 28, 27, 20, 12, 10, 10] },
  { name: "Technology", color: "#6f86f7", values: [30, 30, 30, 28, 24, 22, 22] },
  { name: "Energy", color: "#a9b6fb", values: [10, 10, 11, 12, 12, 12, 12] },
  { name: "Healthcare", color: "#1c8f80", values: [17, 17, 17, 20, 26, 28, 28] },
  { name: "Staples", color: "#7cc4b8", values: [15, 15, 15, 20, 26, 28, 28] },
];

export function WeightsViz() {
  const width = 360, height = 120, n = SERIES[0].values.length;
  const columnTotals = Array.from({ length: n }, (_, i) => SERIES.reduce((sum, s) => sum + s.values[i], 0));
  const x = (i: number) => (i / (n - 1)) * width;
  const share = (upTo: number, i: number) =>
    SERIES.slice(0, upTo).reduce((sum, s) => sum + s.values[i], 0) / columnTotals[i];
  const paths = SERIES.map((series, k) => {
    const top = Array.from({ length: n }, (_, i) => `${x(i)},${(1 - share(k + 1, i)) * height}`);
    const bottom = Array.from({ length: n }, (_, i) => `${x(i)},${(1 - share(k, i)) * height}`).reverse();
    return { ...series, d: `M${top.join(" L")} L${bottom.join(" L")} Z` };
  });
  return (
    <figure>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" role="img" aria-label="Illustration: index weights shifting from financials toward defensive sectors">
        {paths.map((p) => <path key={p.name} d={p.d} fill={p.color} stroke="#fff" strokeWidth={0.6} />)}
      </svg>
      <figcaption className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted">
        {SERIES.map((s) => (
          <span key={s.name} className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-sm" style={{ background: s.color }} />{s.name}
          </span>
        ))}
        <span>Illustration: weights rotate to defensives as stress rises</span>
      </figcaption>
    </figure>
  );
}

const LOSSES = [
  { name: "Loans", value: -1.6 },
  { name: "Bonds", value: -13.8 },
  { name: "Derivatives", value: -4.1 },
  { name: "Equity", value: -12.2 },
];

export function StressViz() {
  return (
    <figure className="space-y-2">
      {LOSSES.map((row) => (
        <div key={row.name} className="grid grid-cols-[84px_1fr_52px] items-center gap-3 text-sm">
          <span>{row.name}</span>
          <div className="h-2.5 rounded-full bg-track">
            <div className="h-2.5 rounded-full" style={{ width: `${(Math.abs(row.value) / 15) * 100}%`, background: SEVERITY[Math.min(9, Math.round(Math.abs(row.value) / 1.6))] }} />
          </div>
          <span className="text-right tabular-nums">{row.value}%</span>
        </div>
      ))}
      <figcaption className="pt-1 text-xs text-muted">Sample run: credit event, impact 9, on the 60-asset synthetic book</figcaption>
    </figure>
  );
}
