import StressPanel from "../../components/StressPanel";
import { PageHeader } from "../../components/ui";

export default function Page() {
  return (
    <>
      <PageHeader title="Module B: strategic stress test" description="High-impact events shock a synthetic wholesale-banking book. See portfolio value before and after." />
      <StressPanel />
    </>
  );
}
