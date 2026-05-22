"use client";

import PayrollRunCreateForm from "@/features/payroll/payroll-run-create-form";

export default function PayrollPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Payroll</h1>
        <p className="mt-1 text-sm text-slate-600">
          Create and manage payroll runs for assigned workers.
        </p>
      </div>

      <PayrollRunCreateForm />
    </div>
  );
}
