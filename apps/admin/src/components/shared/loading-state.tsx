export default function LoadingState({
  title = "Loading",
  description = "Please wait while we prepare this view.",
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="grid min-h-[50vh] place-items-center">
      <div className="rounded-3xl border border-[#ddd3be] bg-[#fffaf0]/85 p-8 text-center shadow-sm">
        <div className="mx-auto mb-5 h-12 w-12 animate-spin rounded-full border-4 border-[#e8d7bd] border-t-[#c96f3c]" />
        <h2 className="font-display text-xl font-semibold text-[#17211a]">{title}</h2>
        <p className="mt-2 max-w-sm text-sm text-[#687267]">{description}</p>
      </div>
    </div>
  );
}
