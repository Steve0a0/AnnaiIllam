/**
 * Full-viewport branded loading screen.
 * Used by ProtectedRoute while the auth store rehydrates from storage.
 * Background matches the sidebar so the transition into the dashboard feels seamless.
 */
export default function FullPageLoader() {
  return (
    <div
      className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-8"
      style={{ background: "var(--color-brand-900)" }}
    >
      {/* Wordmark */}
      <div className="flex flex-col items-center gap-1 select-none">
        <span
          className="text-2xl font-semibold tracking-tight"
          style={{ color: "var(--color-brand-300)" }}
        >
          Annai Illam
        </span>
        <span
          className="text-xs tracking-widest uppercase"
          style={{ color: "var(--color-brand-400)", opacity: 0.6 }}
        >
          Admin
        </span>
      </div>

      {/* Spinner: thin ring, brand-700 track, brand-300 arc */}
      <div
        className="h-8 w-8 animate-spin rounded-full border-2"
        style={{
          borderColor: "var(--color-brand-700)",
          borderTopColor: "var(--color-brand-300)",
        }}
      />
    </div>
  );
}
