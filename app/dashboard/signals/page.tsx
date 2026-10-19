import SignalsPanel from "../../components/SignalsPanel";
import { PageHeader } from "../../components/ui";

export default function Page() {
  return (
    <>
      <PageHeader title="Risk signals" description="The engine's structured output: sentiment, event type and impact for every item, with the working behind each score." />
      <SignalsPanel />
    </>
  );
}
