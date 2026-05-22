import Button from "@/components/ui/button";

export default function ErrorState({
  title = "Something went wrong",
  description = "Try again, or contact support if the issue continues.",
  onRetry,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-3xl border border-red-200 bg-red-50 p-8">
      <p className="font-display text-lg font-semibold text-red-950">{title}</p>
      <p className="mt-2 text-sm leading-6 text-red-800">{description}</p>
      {onRetry ? (
        <div className="mt-5">
          <Button type="button" variant="secondary" onClick={onRetry}>
            Retry
          </Button>
        </div>
      ) : null}
    </div>
  );
}
