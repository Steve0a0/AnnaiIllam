"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, type LucideIcon } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar";

export type NavGroup = {
  label: string;
  items: {
    label: string;
    href: string;
    icon: LucideIcon;
    sub?: {
      label: string;
      href: string;
    }[];
  }[];
};

export function NavMain({ groups }: { groups: NavGroup[] }) {
  const pathname = usePathname();

  return (
    <>
      {groups.map((group) => (
        <SidebarGroup key={group.label}>
          <SidebarGroupLabel>{group.label}</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {group.items.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
                const isGroupActive = item.sub
                  ? item.sub.some((sub) => pathname === sub.href || pathname.startsWith(sub.href + "/"))
                  : isActive;

                if (item.sub) {
                  return (
                    <Collapsible
                      key={item.href}
                      asChild
                      defaultOpen={isGroupActive}
                      className="group/collapsible"
                    >
                      <SidebarMenuItem>
                        <CollapsibleTrigger asChild>
                          <SidebarMenuButton tooltip={item.label} isActive={isGroupActive}>
                            <item.icon />
                            <span className="group-data-[collapsible=icon]:hidden">
                              {item.label}
                            </span>
                            <ChevronRight className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90 group-data-[collapsible=icon]:hidden" />
                          </SidebarMenuButton>
                        </CollapsibleTrigger>
                        <CollapsibleContent>
                          <SidebarMenuSub>
                            {item.sub.map((subItem) => {
                              const isSubActive =
                                pathname === subItem.href ||
                                pathname.startsWith(subItem.href + "/");

                              return (
                                <SidebarMenuSubItem key={subItem.href}>
                                  <SidebarMenuSubButton asChild isActive={isSubActive}>
                                    <Link href={subItem.href}>
                                      <span>{subItem.label}</span>
                                    </Link>
                                  </SidebarMenuSubButton>
                                </SidebarMenuSubItem>
                              );
                            })}
                          </SidebarMenuSub>
                        </CollapsibleContent>
                      </SidebarMenuItem>
                    </Collapsible>
                  );
                }

                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton asChild tooltip={item.label} isActive={isActive}>
                      <Link href={item.href}>
                        <item.icon />
                        <span className="group-data-[collapsible=icon]:hidden">
                          {item.label}
                        </span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      ))}
    </>
  );
}
