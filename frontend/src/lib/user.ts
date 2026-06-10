import { useGet } from "@/lib/api";
import useAuthUser from "react-auth-kit/hooks/useAuthUser";
import { z } from "zod";

export const userSchema = z.object({
  username: z.string(),
  full_name: z.string(),
  profile_image_url: z.string(),
});

export type User = z.infer<typeof userSchema>;

export function useUser(username: string) {
  const { data, error, isLoading } = useGet<User>("u/info", userSchema, [
    username,
  ]);

  return {
    user: data,
    isLoading,
    error: error,
  };
}

export function useCurrentUsername() {
  const authUser = useAuthUser<{ sub: string }>();
  return authUser?.sub || "";
}

export function useCurrentUser() {
  const current_username = useCurrentUsername();
  if (!current_username) {
    return {
      isLoading: false,
      error: null,
      user: null,
    };
  }
  return useUser(current_username);
}
