import * as React from "react";

import { NavTabs } from "@/components/sidebar/nav-tabs";
import { Sidebar, SidebarContent, SidebarRail } from "@/components/ui/sidebar";
import { NavSecondary } from "@/components/sidebar/nav-secondary";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar className="border-r-0 bg-white" {...props}>
      <SidebarContent className="bg-white">
        <NavTabs />
        {/*<NavHistory />
        <AccountButton />
        <NavWorkspaces workspaces={data.workspaces} /> */}
        <NavSecondary className="mt-auto" />
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  );
}
