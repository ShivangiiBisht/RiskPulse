import Link from "next/link";
import Logo from "./components/Logo";
import { StressViz, WeightsViz } from "./components/landing/ModuleViz";
import { ImpactBadge, primaryButtonClass, SeverityScale } from "./components/ui";

const STEPS = [
  { title: "Ingest", body: "Google News, GDELT, Finnhub and a tweet replay are cleaned, de-duplicated and linked to the 18 tracked stocks.", sample: "AAPL · google_news · 14:30" },
  { title: "Understand", body: "FinBERT scores sentiment, a taxonomy names the event, and an explainable formula sets impact from 1 to 10.", sample: "-0.96 · Credit Event · 8" },
  { title: "Rebalance", body: "Decayed sentiment, sector contagion and a market effect set index weights, within bounds and a turnover cap.", sample: "C 5.9% → 2.2%" },
  { title: "Stress test", body: "Events scoring 7 or more shock a synthetic book of loans, bonds, derivatives and equity.", sample: "Book value -9.4%" },
];

const DIFFERENCES = [
  { title: "Every score shows its working", body: "Each signal keeps its headline, model, confidence and the full impact breakdown, so a number can be defended in one click." },
  { title: "Shocks spread to sector peers", body: "A credit event at one bank lowers the effective sentiment of the other banks, even when their own news is quiet." },
  { title: "One regime links both modules", body: "Recent severe negative news sets a normal, elevated or crisis regime. The index rotates away from high-beta sectors and the stress test fires on its own." },
  { title: "A sandbox for what-if questions", body: "Type any headline or replay a synthetic crisis and watch signals, weights, regime and portfolio loss update together." },
];

const SIGNAL_ROWS = [
  { label: "Entity", value: "MARKET" },
  { label: "Event", value: "Credit Event" },
];

export default function Landing() {
  return (
    <div>
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <Logo />
        <nav className="flex items-center gap-6 text-sm">
          <a href="#how" className="hidden text-muted hover:text-ink sm:inline">How it works</a>
          <a href="#different" className="hidden text-muted hover:text-ink sm:inline">What is different</a>
          <a href="#modules" className="hidden text-muted hover:text-ink sm:inline">Modules</a>
          <Link href="/dashboard" className={primaryButtonClass}>Open dashboard</Link>
        </nav>
      </header>

      <main>
        <section className="mx-auto grid max-w-6xl gap-10 px-6 pb-14 pt-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:pt-16">
          <div>
            <h1 className="font-serif text-5xl font-medium leading-[1.05] tracking-tight sm:text-6xl">
              Headlines in.<br />Risk decisions out.
            </h1>
            <p className="mt-6 max-w-xl text-lg text-muted">
              RiskPulse reads financial news and social posts, scores each item for sentiment, event type and market
              impact, then rebalances an index and stress-tests a bank&apos;s portfolio from the result.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/dashboard" className={primaryButtonClass}>Open dashboard</Link>
              <Link href="/dashboard/sandbox" className="rounded-sm border border-line-strong bg-surface px-4 py-2 text-sm font-medium hover:bg-surface-2">
                Replay a bank run
              </Link>
            </div>
          </div>

          {/* Example signal: one headline resolving into a structured signal */}
          <div className="rounded-md border border-line bg-surface p-5" aria-label="Example of one headline turned into a risk signal">
            <div className="text-xs text-muted">Example signal, sample data</div>
            <p className="rise mt-2 font-serif text-xl leading-snug" style={{ animationDelay: "0.2s" }}>
              &ldquo;Regional lender halts withdrawals as depositors rush for exits&rdquo;
            </p>
            <dl className="mt-5 space-y-3 text-sm">
              {SIGNAL_ROWS.map((row, index) => (
                <div key={row.label} className="rise flex justify-between border-t border-line pt-3" style={{ animationDelay: `${0.7 + index * 0.25}s` }}>
                  <dt className="text-muted">{row.label}</dt><dd className="font-medium">{row.value}</dd>
                </div>
              ))}
              <div className="rise flex items-center justify-between border-t border-line pt-3" style={{ animationDelay: "1.2s" }}>
                <dt className="text-muted">Sentiment</dt>
                <dd className="flex items-center gap-2">
                  <span className="relative h-1.5 w-28 rounded-full bg-track">
                    <span className="fill absolute right-1/2 top-0 h-1.5 w-[48%] origin-right rounded-full bg-neg" style={{ animationDelay: "1.3s" }} />
                  </span>
                  <span className="tabular-nums">-0.96</span>
                </dd>
              </div>
              <div className="rise flex items-center justify-between border-t border-line pt-3" style={{ animationDelay: "1.5s" }}>
                <dt className="text-muted">Impact</dt><dd><ImpactBadge impact={8} /> of 10</dd>
              </div>
            </dl>
            <div className="rise mt-5 grid grid-cols-2 gap-3 border-t border-line pt-4 text-sm" style={{ animationDelay: "1.9s" }}>
              <div>
                <div className="text-xs text-muted">Index response</div>
                <div>C <span className="text-neg">-3.6 pp</span>, GS <span className="text-neg">-2.6 pp</span></div>
                <div>WMT <span className="text-pos">+4.6 pp</span>, KO <span className="text-pos">+3.3 pp</span></div>
              </div>
              <div>
                <div className="text-xs text-muted">Stress test (impact 7+)</div>
                <div className="font-medium text-crisis">Book value -9.4%</div>
                <div className="text-muted">Regime: crisis</div>
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 pb-16" aria-label="Impact scale">
          <SeverityScale threshold={7} />
          <p className="mt-2 text-sm text-muted">Every event lands on one 1 to 10 impact scale: negligible on the left, systemic on the right.</p>
        </section>

        <section id="how" className="border-t border-line bg-surface">
          <div className="mx-auto max-w-6xl px-6 py-16">
            <h2 className="font-serif text-3xl">From text to action in four steps</h2>
            <div className="mt-10 grid gap-8 md:grid-cols-4">
              {STEPS.map((step, index) => (
                <div key={step.title} className="border-t-2 border-ink pt-4">
                  <div className="font-serif text-4xl text-line-strong">{index + 1}</div>
                  <h3 className="mt-2 font-serif text-xl">{step.title}</h3>
                  <p className="mt-2 text-sm text-muted">{step.body}</p>
                  <p className="mt-4 rounded-sm bg-surface-2 px-2 py-1.5 font-mono text-xs">{step.sample}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="different" className="mx-auto max-w-6xl px-6 py-16">
          <h2 className="font-serif text-3xl">What is different</h2>
          <div className="mt-8">
            {DIFFERENCES.map((item) => (
              <div key={item.title} className="grid gap-2 border-t border-line py-6 md:grid-cols-[300px_1fr] md:gap-10">
                <h3 className="font-serif text-xl">{item.title}</h3>
                <p className="max-w-xl text-muted">{item.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="modules" className="border-t border-line bg-surface">
          <div className="mx-auto max-w-6xl px-6 py-16">
            <h2 className="font-serif text-3xl">Two modules, one engine</h2>
            <p className="mt-2 max-w-2xl text-muted">The same signals drive a fast tactical decision and a slower strategic one.</p>
            <div className="mt-8 grid gap-6 lg:grid-cols-2">
              <article className="rounded-md border border-line p-6">
                <h3 className="font-serif text-2xl">Module A: tactical rebalancer</h3>
                <p className="mb-5 mt-2 text-sm text-muted">Rebalances an 18-stock index after every batch of signals, with weight bounds, a turnover cap and a risk-off tilt in stress.</p>
                <WeightsViz />
                <Link href="/dashboard/rebalancer" className="mt-5 inline-block text-sm font-medium text-cobalt hover:underline">Open the rebalancer</Link>
              </article>
              <article className="rounded-md border border-line p-6">
                <h3 className="font-serif text-2xl">Module B: strategic stress test</h3>
                <p className="mb-5 mt-2 text-sm text-muted">Applies event-specific shocks to loans, bonds, derivatives and equity, and shows portfolio value before and after.</p>
                <StressViz />
                <Link href="/dashboard/stress" className="mt-5 inline-block text-sm font-medium text-cobalt hover:underline">Open the stress test</Link>
              </article>
            </div>
          </div>
        </section>

        <section className="bg-ink text-white">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-6 px-6 py-14">
            <div>
              <h2 className="font-serif text-3xl">Break something and watch it react</h2>
              <p className="mt-2 max-w-xl text-white/70">Replay a bank run, an oil shock or a hawkish central bank, or type your own headline.</p>
            </div>
            <Link href="/dashboard/sandbox" className="rounded-sm bg-white px-5 py-2.5 text-sm font-medium text-ink hover:bg-white/90">Open the sandbox</Link>
          </div>
        </section>
      </main>

      <footer className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-6 py-8 text-sm text-muted">
        <span>S&amp;P Global &amp; Crisil Campus Hackathon. Public data and synthetic portfolio only.</span>
        <a className="hover:text-ink" href="https://github.com/ShivangiiBisht/random" target="_blank" rel="noreferrer">Source on GitHub</a>
      </footer>
    </div>
  );
}
