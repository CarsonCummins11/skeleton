import { createRootRouteWithContext, Outlet } from "@tanstack/react-router";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/sidebar/app-sidebar";

interface RouterContext {
  is_authenticated: boolean;
  username: string;
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: () => (
    <SidebarProvider defaultOpen={false}>
      <AppSidebar />
      <Outlet />
    </SidebarProvider>
  ),
});
