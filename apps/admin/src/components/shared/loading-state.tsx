export default function LoadingState({
  title = "Loading",
  description = "Please wait while we prepare this view.",
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="grid min-h-[50vh] place-items-center">
      <div className="flex flex-col items-center gap-5 rounded-2xl border border-border bg-card px-10 py-9 text-center shadow-sm">
        {/* Spinner using brand green tokens */}
        <div
          className="h-11 w-11 animate-spin rounded-full border-[3px]"
          style={{
            borderColor: "var(--color-brand-100)",
            borderTopColor: "var(--color-brand-500)",
          }}
        />
        <div className="space-y-1">
          <h2 className="text-sm font-semibold text-foreground">{title}</h2>
          <p className="max-w-xs text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
    </div>
  );
}
