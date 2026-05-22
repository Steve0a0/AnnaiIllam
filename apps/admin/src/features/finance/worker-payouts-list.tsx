"use client";

import { useWorkerPayouts } from "@/features/finance/use-worker-payouts";
import FinanceLoading from "@/features/finance/finance-loading";
import FinanceError from "@/features/finance/finance-error";
import FinanceEmpty from "@/features/finance/finance-empty";
import StatusBadge from "@/components/shared/status-badge";
import UpdateWorkerPayoutStatus from "@/features/finance/update-worker-payout-status";
import { formatCurrency } from "@/lib/format-currency";

export default function WorkerPayoutsList({
  payrollItemId,
}: {
  payrollItemId: number;
}) {
  const { data, isLoading, isError, error, refetch } =
    useWorkerPayouts(payrollItemId);

  if (isLoading) {
    return <FinanceLoading />;
  }

  if (isError) {
    return <FinanceError message={error?.message} />;
  }

  const payouts = data?.data ?? [];

  if (!payouts.length) {
    return <FinanceEmpty label="worker payouts" />;
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-white shadow-sm">
      <table className="min-w-full divide-y divide-border">
        <thead className="bg-secondary">
          <tr>
            {["Payout ID", "Amount", "Mode", "Status", "Reference", "Paid At", "Action"].map((heading) => (
              <th key={heading} className="h-11 px-4 text-left text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
                {heading}
              </th>
            ))}
          </tr>
        </thead>

        <tbody className="divide-y divide-border">
          {payouts.map((item) => (
            <tr key={item.id} className="transition-colors hover:bg-secondary">
              <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{item.id}</td>
              <td className="px-4 py-3 font-mono text-sm text-foreground">
                {formatCurrency(item.amount)}
              </td>
              <td className="px-4 py-3 text-sm text-foreground capitalize">
                {item.payout_mode}
              </td>
              <td className="px-4 py-3">
                <StatusBadge value={item.payout_status} />
              </td>
              <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                {item.transaction_reference ?? "—"}
              </td>
              <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                {item.paid_at ?? "—"}
              </td>
              <td className="px-4 py-3">
                <UpdateWorkerPayoutStatus
                  payoutId={item.id}
                  currentStatus={item.payout_status}
                  onSuccess={() => refetch()}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
