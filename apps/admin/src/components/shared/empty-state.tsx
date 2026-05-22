import Button from "@/components/ui/button";

export default function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
}: {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="rounded-3xl border border-dashed border-[#d5c7ad] bg-[#fffaf0]/70 p-10 text-center">
      <p className="font-display text-lg font-semibold text-[#17211a]">{title}</p>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[#687267]">{description}</p>
      {actionLabel ? (
        <div className="mt-6">
          <Button type="button" onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
