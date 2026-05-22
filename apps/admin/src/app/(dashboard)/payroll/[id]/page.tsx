"use client";

import { useParams } from "next/navigation";
import PayrollRunDetailView from "@/features/payroll/payroll-run-detail-view";

export default function PayrollRunDetailPage() {
  const params = useParams();
  const payrollRunId = Number(params.id);

  return <PayrollRunDetailView payrollRunId={payrollRunId} />;
}
