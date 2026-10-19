import IngestionPanel from "../../components/IngestionPanel";
import { PageHeader } from "../../components/ui";

export default function Page() {
  return (
    <>
      <PageHeader title="Ingestion" description="Collect news and social text, clean it, link it to stocks and score it. Scoring runs automatically after every job." />
      <IngestionPanel />
    </>
  );
}
