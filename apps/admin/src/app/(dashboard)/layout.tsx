import AppSidebar from "@/components/layout/sidebar";
import Topbar from "@/components/layout/topbar";
import LegalFooter from "@/components/layout/legal-footer";
import DashboardBootstrap from "@/components/shared/dashboard-bootstrap";
import ProtectedRoute from "@/components/shared/protected-route";
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <DashboardBootstrap>
        <SidebarProvider>
          <AppSidebar />
          <SidebarInset>
            <Topbar />
            <main className="flex-1 px-4 py-6 md:px-8 md:py-8">{children}</main>
            <LegalFooter />
          </SidebarInset>
        </SidebarProvider>
      </DashboardBootstrap>
    </ProtectedRoute>
  );
}
