export default function RequirementsError({
  message,
}: {
  message?: string;
}) {
  return (
    <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-red-700">
      <h3 className="text-lg font-semibold">Failed to load requirements</h3>
      <p className="mt-2 text-sm">
        {message || "Something went wrong while fetching requirements."}
      </p>
    </div>
  );
}
