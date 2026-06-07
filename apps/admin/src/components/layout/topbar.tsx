"use client";

import { useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AlertTriangle, Bell, CalendarOff, CreditCard, LogOut, Search } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { authStorage } from "@/lib/auth-storage";
import { useAuthStore } from "@/store/auth-store";
import { authService } from "@/services/auth.service";
import { useDashboardAlerts } from "@/features/dashboard/use-dashboard-alerts";

const pageLabels: Record<string, string> = {
  "/dashboard":    "Dashboard",
  "/clients":      "Clients",
  "/workers":      "Workers",
  "/requirements": "Requests",
  "/assignments":  "Assignments",
  "/attendance":   "Attendance",
  "/complaints":   "Complaints",
  "/settings":     "Settings",
};

function getInitials(name?: string | null) {
  if (!name) return "A";
  return name
    .split(/\s+/)
    .map((p) => p[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export default function Topbar() {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const { data: alertsResp } = useDashboardAlerts();
  const alerts = alertsResp?.data;
  const totalAlerts =
    (alerts?.open_complaints?.length ?? 0) +
    (alerts?.overdue_complaints?.length ?? 0) +
    (alerts?.missing_attendance?.length ?? 0) +
    (alerts?.unpaid_invoices?.length ?? 0);

  // Badge only shows count that arrived AFTER the dropdown was last opened.
  // Persisted to localStorage so refresh doesn't bring the badge back.
  const [seenCount, setSeenCount] = useState<number>(() => {
    if (typeof window === "undefined") return 0;
    return Number(localStorage.getItem("admin_alerts_seen") ?? 0);
  });
  const badgeCount = Math.max(0, totalAlerts - seenCount);

  function handleBellOpenChange(open: boolean) {
    if (open) {
      setSeenCount(totalAlerts);
      localStorage.setItem("admin_alerts_seen", String(totalAlerts));
    }
  }

  const segment = "/" + (pathname.split("/")[1] ?? "");
  const pageLabel = pageLabels[segment] ?? "Workspace";

  async function handleLogout() {
    try {
      if (refreshToken) await authService.logout(refreshToken);
    } catch {
      // ignore
    } finally {
      authStorage.clear();
      clearAuth();
      router.replace("/login");
    }
  }

  return (
    <header className="sticky top-0 z-20 h-14 shrink-0 border-b border-border bg-white/90 backdrop-blur-md transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12">
      <div className="flex h-full items-center gap-3 px-4 md:px-6">
        <SidebarTrigger className="-ml-1 text-muted-foreground hover:text-foreground" />
        <Separator orientation="vertical" className="h-5" />

        <div className="flex-1 min-w-0">
          <p className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground">Admin</p>
          <p className="truncate font-display text-xl font-medium text-foreground leading-tight">
            {pageLabel}
          </p>
        </div>

        <div className="relative hidden w-full max-w-xs lg:block">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            aria-label="Search admin records"
            placeholder="Search requests, workers, clients"
            className="h-9 rounded-lg border-transparent bg-muted pl-9 text-sm focus:border-border focus:bg-white"
          />
        </div>

        <DropdownMenu onOpenChange={handleBellOpenChange}>
          <DropdownMenuTrigger asChild>
            <button
              aria-label="View notifications"
              className="relative flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted/30 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Bell className="h-4 w-4" />
              {badgeCount > 0 && (
                <span className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[9px] font-bold leading-none text-white">
                  {badgeCount > 99 ? "99+" : badgeCount}
                </span>
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel className="flex items-center justify-between">
              <span>Alerts</span>
              {totalAlerts > 0 && (
                <span className="rounded-full bg-destructive px-1.5 py-0.5 text-[10px] font-bold text-white">
                  {totalAlerts}
                </span>
              )}
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            {totalAlerts === 0 ? (
              <div className="px-3 py-6 text-center">
                <p className="text-sm font-medium text-foreground">All clear</p>
                <p className="mt-0.5 text-xs text-muted-foreground">No active alerts right now.</p>
              </div>
            ) : (
              <>
                {(alerts?.open_complaints?.length ?? 0) > 0 && (
                  <DropdownMenuItem
                    className="cursor-pointer gap-3"
                    onClick={() => router.push("/complaints")}
                  >
                    <AlertTriangle className="h-4 w-4 shrink-0 text-amber-500" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium">
                        {alerts!.open_complaints.length} new complaint{alerts!.open_complaints.length !== 1 ? "s" : ""}
                      </p>
                      <p className="text-xs text-muted-foreground">Awaiting admin review</p>
                    </div>
                  </DropdownMenuItem>
                )}
                {(alerts?.overdue_complaints?.length ?? 0) > 0 && (
                  <DropdownMenuItem
                    className="cursor-pointer gap-3"
                    onClick={() => router.push("/complaints")}
                  >
                    <AlertTriangle className="h-4 w-4 shrink-0 text-destructive" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium">
                        {alerts!.overdue_complaints.length} overdue complaint{alerts!.overdue_complaints.length !== 1 ? "s" : ""}
                      </p>
                      <p className="text-xs text-muted-foreground">Past SLA — needs resolution</p>
                    </div>
                  </DropdownMenuItem>
                )}
                {(alerts?.missing_attendance?.length ?? 0) > 0 && (
                  <DropdownMenuItem
                    className="cursor-pointer gap-3"
                    onClick={() => router.push("/attendance")}
                  >
                    <CalendarOff className="h-4 w-4 shrink-0 text-amber-500" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium">
                        {alerts!.missing_attendance.length} worker{alerts!.missing_attendance.length !== 1 ? "s" : ""} not checked in
                      </p>
                      <p className="text-xs text-muted-foreground">Today&apos;s attendance missing</p>
                    </div>
                  </DropdownMenuItem>
                )}
                {(alerts?.unpaid_invoices?.length ?? 0) > 0 && (
                  <DropdownMenuItem
                    className="cursor-pointer gap-3"
                    onClick={() => router.push("/requirements")}
                  >
                    <CreditCard className="h-4 w-4 shrink-0 text-blue-500" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium">
                        {alerts!.unpaid_invoices.length} unpaid invoice{alerts!.unpaid_invoices.length !== 1 ? "s" : ""}
                      </p>
                      <p className="text-xs text-muted-foreground">Pending client payment</p>
                    </div>
                  </DropdownMenuItem>
                )}
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              aria-label="Account menu"
              className="rounded-full p-0.5 transition-colors hover:bg-muted/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Avatar className="h-9 w-9 border-2 border-[var(--color-brand-100)]">
                <AvatarFallback className="bg-primary text-xs font-medium text-primary-foreground">
                  {getInitials(user?.name)}
                </AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel className="font-normal">
              <p className="text-xs font-semibold">{user?.name ?? user?.email ?? "Admin"}</p>
              <p className="text-[10px] uppercase tracking-widest text-muted-foreground">
                {user?.role ?? "admin"}
              </p>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="cursor-pointer text-destructive focus:bg-destructive/10 focus:text-destructive"
              onClick={handleLogout}
            >
              <LogOut className="mr-2 h-4 w-4" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
