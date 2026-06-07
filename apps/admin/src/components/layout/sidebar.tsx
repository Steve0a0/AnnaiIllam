"use client";

import type * as React from "react";
import Link from "next/link";
import {
  Banknote,
  BarChart3,
  Building2,
  CalendarCheck,
  ClipboardList,
  Landmark,
  LayoutDashboard,
  MessageCircleWarning,
  Scale,
  ScrollText,
  Settings,
  ShieldCheck,
  Timer,
  Users,
} from "lucide-react";
import { useAuthStore } from "@/store/auth-store";
import { NavMain, type NavGroup } from "@/components/layout/nav-main";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
  SidebarSeparator,
} from "@/components/ui/sidebar";

const navGroups: NavGroup[] = [
  {
    label: "Operations",
    items: [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      {
        label: "Requests",
        href: "/requirements",
        icon: ClipboardList,
        sub: [
          { label: "All Requests", href: "/requirements" },
          { label: "Assignments", href: "/assignments" },
        ],
      },
      { label: "Workers", href: "/workers", icon: Users },
      { label: "Clients", href: "/clients", icon: Building2 },
      { label: "Attendance", href: "/attendance", icon: CalendarCheck },
    ],
  },
  {
    label: "Finance",
    items: [
      { label: "Payroll", href: "/payroll", icon: Banknote },
      { label: "Finance", href: "/finance", icon: Landmark },
    ],
  },
  {
    label: "Management",
    items: [
      { label: "Disputes", href: "/disputes", icon: Scale },
      { label: "Complaints", href: "/complaints", icon: MessageCircleWarning,
        sub: [
          { label: "All Complaints", href: "/complaints" },
          { label: "Replacements", href: "/replacements" },
        ],
      },
      { label: "Reports", href: "/reports", icon: BarChart3 },
      { label: "Audit Log", href: "/audit", icon: ScrollText },
      { label: "SLA Policies", href: "/sla", icon: Timer },
      { label: "Admin Users", href: "/admin-users", icon: ShieldCheck },
      { label: "Settings", href: "/settings", icon: Settings },
    ],
  },
];

function getInitials(name?: string | null) {
  if (!name) return "A";
  return name
    .split(/\s+/)
    .map((p) => p[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export default function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const user = useAuthStore((s) => s.user);
  const isSuperAdmin = user?.permission_group === "super_admin";

  return (
    <Sidebar
      collapsible="icon"
      className="border-r border-sidebar-border"
      {...props}
    >
      <SidebarHeader className="px-3 pb-2 pt-3 group-data-[collapsible=icon]:px-0">
        <Link
          href="/dashboard"
          className="flex h-16 items-center gap-2.5 rounded-lg px-3 transition hover:bg-white/10 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-0"
        >
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-(--color-brand-600) text-xs font-semibold text-white">
            AI
          </div>
          <div className="flex flex-col group-data-[collapsible=icon]:hidden">
            <span className="font-display text-base font-semibold leading-none text-sidebar-foreground">
              Annai Illam
            </span>
            <span className="mt-1 text-[10px] font-medium uppercase tracking-widest text-white/35">
              Operations
            </span>
          </div>
        </Link>
      </SidebarHeader>

      <SidebarSeparator />

      <SidebarContent>
        <NavMain
          groups={navGroups.map((group) => ({
            ...group,
            items: group.items.filter(
              (item) => item.href !== "/admin-users" || isSuperAdmin
            ),
          }))}
        />
      </SidebarContent>

      <SidebarSeparator />

      <SidebarFooter className="px-3 pb-3 pt-2 group-data-[collapsible=icon]:px-0">
        {user ? (
          <div className="flex items-center gap-2.5 rounded-lg px-1 py-2 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-0">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-(--color-brand-100) bg-primary text-xs font-medium text-primary-foreground">
              {getInitials(user.name)}
            </div>
            <div className="min-w-0 group-data-[collapsible=icon]:hidden">
              <p className="truncate text-sm font-medium leading-none text-sidebar-foreground">
                {user.name ?? user.email}
              </p>
              <p className="mt-1 text-[10px] uppercase tracking-widest text-white/40 leading-none">
                {user.role}
              </p>
            </div>
          </div>
        ) : null}
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}
