import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import createStore from "react-auth-kit/createStore";
import AuthProvider from "react-auth-kit";
import useIsAuthenticated from "react-auth-kit/hooks/useIsAuthenticated";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "@tanstack/react-router";
import { router } from "./router";
import { useCurrentUsername } from "@/lib/user";

function InnerApp() {
  const isAuthenticated = useIsAuthenticated();
  const username = isAuthenticated ? useCurrentUsername() : "";
  return (
    <RouterProvider
      router={router}
      context={{ is_authenticated: isAuthenticated, username: username }}
    />
  );
}

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

const auth_store = createStore({
  authName: "_auth",
  authType: "cookie",
  cookieDomain: window.location.hostname,
  cookieSecure: window.location.protocol === "https:",
});

const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider store={auth_store}>
        <InnerApp />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>
);
