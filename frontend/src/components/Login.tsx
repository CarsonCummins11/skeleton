import { useForm } from "react-hook-form";
import { jwtDecode } from "jwt-decode";
import useSignIn from "react-auth-kit/hooks/useSignIn";
import Box from "@/components/ui_lib/Box";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { API_URL } from "@/env";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";

const LoginInformation = z.object({
  username: z.string(),
  password: z.string(),
});

export default function Login() {
  const form = useForm<z.infer<typeof LoginInformation>>({
    resolver: zodResolver(LoginInformation),
    defaultValues: {
      username: "",
    },
  });
  const signIn = useSignIn();

  function onSubmit(values: z.infer<typeof LoginInformation>) {
    const formData = new FormData();
    formData.append("username", values.username);
    formData.append("password", values.password);
    fetch(API_URL + "/u/login", {
      method: "POST",
      body: formData,
    }).then((response) => {
      if (!response.ok) {
        alert("invalid login credentials");
        throw new Error(`HTTP error: ${response.status}`);
      }
      response.json().then((res) => {
        if (
          signIn({
            auth: {
              token: res.access_token,
              type: "Bearer",
            },
            userState: jwtDecode(res.access_token),
          })
        ) {
          // if there is a redirect url, redirect to it
          const redirectUrl = new URL(window.location.href);
          const redirect = redirectUrl.searchParams.get("redirect");
          if (redirect) {
            redirectUrl.pathname = redirect;
            redirectUrl.searchParams.delete("redirect");
          }
          // otherwise go to /
          else {
            redirectUrl.pathname = "/";
            redirectUrl.searchParams.delete("redirect");
          }
          window.location.href = redirectUrl.toString();
        } else {
          alert("invalid login credentials");
        }
      });
    });
  }
  return (
    <Box className="flex-col max-w-[20rem]">
      <h1 className="text-2xl font-bold mb-4">Sign in</h1>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
          <FormField
            control={form.control}
            name="username"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Username</FormLabel>
                <FormControl>
                  <Input placeholder="Username" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Password</FormLabel>
                <FormControl>
                  <Input placeholder="Password" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button type="submit">Sign in</Button>
        </form>
      </Form>
    </Box>
  );
}
