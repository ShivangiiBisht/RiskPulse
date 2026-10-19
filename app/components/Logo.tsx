import { SEVERITY } from "./ui";

export default function Logo({ size = 22 }: { size?: number }) {
  const bars = [2, 5, 8, 10];
  return (
    <span className="inline-flex items-center gap-2">
      <svg width={size} height={size} viewBox="0 0 22 22" aria-hidden="true">
        {bars.map((level, index) => (
          <rect key={level} x={index * 5.5} y={22 - level * 2} width={4} height={level * 2} fill={SEVERITY[level - 1]} />
        ))}
      </svg>
      <span className="font-serif text-xl font-semibold tracking-tight">RiskPulse</span>
    </span>
  );
}
