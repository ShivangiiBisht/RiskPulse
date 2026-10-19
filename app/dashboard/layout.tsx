import type { Metadata } from "next";
import type { ReactNode } from "react";
import DashboardShell from "../components/DashboardShell";

export const metadata: Metadata = { title: "Dashboard | RiskPulse" };

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return <DashboardShell>{children}</DashboardShell>;
}
