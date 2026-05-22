"use client";

import { useBootstrapUser } from "@/hooks/use-bootstrap-user";

export default function DashboardBootstrap({
  children,
}: {
  children: React.ReactNode;
}) {
  useBootstrapUser();
  return <>{children}</>;
}
