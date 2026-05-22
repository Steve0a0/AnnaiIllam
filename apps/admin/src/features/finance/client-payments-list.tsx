"use client";

import { useClientPayments } from "@/features/finance/use-client-payments";
import FinanceLoading from "@/features/finance/finance-loading";
import FinanceError from "@/features/finance/finance-error";
import FinanceEmpty from "@/features/finance/finance-empty";
import StatusBadge from "@/components/shared/status-badge";
import { formatCurrency } from "@/lib/format-currency";

export default function ClientPaymentsList({
  requirementId,
}: {
  requirementId: number;
}) {
  const { data, isLoading, isError, error } = useClientPayments(requirementId);

  if (isLoading) {
    return <FinanceLoading />;
  }

  if (isError) {
    return <FinanceError message={error?.message} />;
  }

  const payments = data?.data ?? [];

  if (!payments.length) {
    return <FinanceEmpty label="client payments" />;
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Payment ID
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Amount
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Model
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Mode
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Status
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Paid At
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Reference
            </th>
          </tr>
        </thead>

        <tbody className="divide-y divide-slate-100">
          {payments.map((item) => (
            <tr key={item.id}>
              <td className="px-4 py-3 text-sm text-slate-700">{item.id}</td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {formatCurrency(item.amount)}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.payment_model.replaceAll("_", " ")}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.payment_mode}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                <StatusBadge value={item.payment_status} />
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.paid_at ?? "-"}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.reference_note ?? "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
