import RebalancerPanel from "../../components/RebalancerPanel";
import { PageHeader } from "../../components/ui";

export default function Page() {
  return (
    <>
      <PageHeader title="Module A: tactical rebalancer" description="Index weights react to decayed sentiment, sector contagion and the market effect, with a risk-off tilt in stress." />
      <RebalancerPanel />
    </>
  );
}
