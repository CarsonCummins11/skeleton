import { createFileRoute, redirect } from "@tanstack/react-router";
import { SidebarInset, SidebarTrigger } from "@/components/ui/sidebar";

export const Route = createFileRoute("/")({
  beforeLoad: ({ context, location }) => {
    if (!context.is_authenticated) {
      throw redirect({
        to: "/login",
        search: { redirect: location.href },
      });
    }
  },
  component: Index,
});

function Index() {
  return (
    <SidebarInset>
      <header className="flex h-14 shrink-0 items-center gap-2">
        <div className="flex flex-1 items-center gap-2 px-3">
          <SidebarTrigger />
        </div>
      </header>
      <div className="flex flex-1 flex-col gap-4 px-4 py-10 justify-center items-center">
        <h1 className="text-2xl font-bold">Welcome</h1>
        <p className="text-muted-foreground">Your app starts here.</p>
      </div>
    </SidebarInset>
  );
}
