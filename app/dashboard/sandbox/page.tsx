import SandboxPanel from "../../components/SandboxPanel";
import { PageHeader } from "../../components/ui";

export default function Page() {
  return (
    <>
      <PageHeader title="Crisis sandbox" description="Inject a headline or replay a synthetic crisis and watch signals, weights, regime and portfolio loss respond." />
      <SandboxPanel />
    </>
  );
}
