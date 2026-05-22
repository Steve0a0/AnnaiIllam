export default function FinanceError({ message }: { message?: string }) {
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
      {message ?? "Failed to load finance data. Please try again."}
    </div>
  );
}
