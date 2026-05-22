const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/requirements": "Requirements",
  "/assignments": "Assignments",
  "/attendance": "Attendance",
  "/payroll": "Payroll",
  "/finance": "Finance",
  "/complaints": "Complaints",
  "/reports": "Reports",
};

export function getPageTitle(pathname: string): string {
  return PAGE_TITLES[pathname] ?? "Annai Illam Admin";
}

export const APP_NAME = "Annai Illam Admin";
