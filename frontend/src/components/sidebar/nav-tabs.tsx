import { Home } from "lucide-react";
import {
  SidebarGroup,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Link as NavLink } from "@tanstack/react-router";

export function NavTabs() {
  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden">
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton asChild>
            <NavLink to="/">
              <Home className="h-4 w-4" />
              <span>Home</span>
            </NavLink>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarGroup>
  );
}
