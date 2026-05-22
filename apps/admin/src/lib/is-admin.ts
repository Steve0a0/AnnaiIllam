import type { AuthUser } from "@/types/auth";

export function isAdmin(user: AuthUser | null | undefined): boolean {
  return user?.role === "admin";
}
