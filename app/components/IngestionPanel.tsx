"use client";

import { useState } from "react";
import { api, useApi, type Doc, type Job, type Stats } from "../lib/api";
import { buttonClass, Card, ErrorNote, selectClass, shortTime } from "./ui";

const BUTTONS = [
  { label: "Ingest all", path: "/ingest/all" },
  { label: "Google News", path: "/ingest/googlenews" },
  { label: "GDELT", path: "/ingest/gdelt" },
  { label: "Finnhub", path: "/ingest/finnhub" },
  { label: "Tweets (replay)", path: "/ingest/tweets" },
];

export default function IngestionPanel() {
  const [provider, setProvider] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const jobs = useApi<Record<string, Job>>("/ingest/jobs", 2500);
  const stats = useApi<Stats>("/stats", 2500);
  const docs = useApi<Doc[]>(`/documents?limit=40${provider ? `&provider=${provider}` : ""}`, 5000);

  async function start(path: string) {
    try {
      await api(path, { method: "POST" });
      setActionError(null);
      jobs.reload();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Request failed");
    }
  }

  return (
    <div className="space-y-4">
      <ErrorNote message={jobs.error ?? actionError} />
      <Card title="1. Ingest text (news + social) and score it">
        <div className="flex flex-wrap gap-2">
          {BUTTONS.map((button) => (
            <button key={button.path} className={buttonClass} onClick={() => start(button.path)}>
              {button.label}
            </button>
          ))}
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          Every ingestion job is followed automatically by NLP scoring (sentiment, event type, impact).
        </p>
        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {Object.entries(jobs.data ?? {}).map(([name, job]) => (
            <div key={name} className="rounded border border-zinc-200 p-3 text-sm dark:border-zinc-800">
              <div className="flex justify-between">
                <span className="font-medium">{name}</span>
                <span className={job.status === "done" ? "text-green-600" : job.status === "failed" ? "text-red-600" : "text-amber-600"}>
                  {job.status}
                </span>
              </div>
              {job.stats?.seen !== undefined && (
                <p className="mt-1 text-xs text-zinc-500">
                  seen {job.stats.seen} · new {job.stats.inserted} · dup {job.stats.duplicates}
                </p>
              )}
              {job.stats?.scoring && (
                <p className="text-xs text-zinc-500">
                  scored {job.stats.scoring.documents} docs → {job.stats.scoring.signals} signals (
                  {job.stats.scoring.sentiment_backend})
                </p>
              )}
              {job.error && <p className="mt-1 break-words text-xs text-red-600">{job.error}</p>}
            </div>
          ))}
        </div>
      </Card>

      <Card title="2. Database">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 text-sm">
          <Stat label="Documents" value={stats.data?.total} />
          <Stat label="Signals" value={stats.data?.signals} />
          <Stat label="Unscored" value={stats.data?.unscored} />
          <div>
            <div className="text-zinc-500">By provider</div>
            {Object.entries(stats.data?.by_provider ?? {}).map(([name, count]) => (
              <div key={name} className="flex justify-between"><span>{name}</span><span>{count}</span></div>
            ))}
          </div>
        </div>
      </Card>

      <Card
        title="3. Latest documents"
        right={
          <select className={selectClass} value={provider} onChange={(e) => setProvider(e.target.value)}>
            {["", "google_news", "gdelt", "finnhub", "tweet_replay", "sandbox"].map((p) => (
              <option key={p} value={p}>{p || "All providers"}</option>
            ))}
          </select>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-zinc-500">
              <tr><th className="py-1 pr-3">Time (UTC)</th><th className="pr-3">Provider</th><th className="pr-3">Tickers</th><th>Text</th></tr>
            </thead>
            <tbody>
              {(docs.data ?? []).length === 0 && (
                <tr><td colSpan={4} className="py-4 text-center text-zinc-500">No documents yet. Click an ingest button.</td></tr>
              )}
              {(docs.data ?? []).map((doc) => (
                <tr key={doc.doc_id} className="border-t border-zinc-200 dark:border-zinc-800">
                  <td className="whitespace-nowrap py-1.5 pr-3 text-zinc-500">{shortTime(doc.published_at)}</td>
                  <td className="pr-3">{doc.provider}</td>
                  <td className="pr-3">{doc.tickers.join(", ") || <span className="text-zinc-400">none</span>}</td>
                  <td>
                    {doc.url ? <a className="hover:underline" href={doc.url} target="_blank" rel="noreferrer">{doc.text}</a> : doc.text}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | undefined }) {
  return (
    <div>
      <div className="text-zinc-500">{label}</div>
      <div className="text-xl font-semibold">{value ?? "-"}</div>
    </div>
  );
}
