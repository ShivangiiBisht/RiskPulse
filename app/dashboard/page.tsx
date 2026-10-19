import OverviewPanel from "../components/OverviewPanel";
import { PageHeader } from "../components/ui";

export default function Page() {
  return (
    <>
      <PageHeader title="Overview" description="Current risk regime, the latest severe events, how the index is tilted and what the stress test shows." />
      <OverviewPanel />
    </>
  );
}
