import ErrorState from "@/components/shared/error-state";

export default function DashboardError({ message }: { message?: string }) {
  return (
    <ErrorState
      title="Failed to load dashboard"
      description={message ?? "Something went wrong while fetching dashboard data."}
    />
  );
}
