export default function ReportsError({ message }: { message?: string }) {
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
      {message ?? "Failed to load report data."}
    </div>
  );
}
