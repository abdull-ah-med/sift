"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input } from "@sift/ui";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import { INVITE_STORAGE_KEY } from "@/lib/invite";

/** Invite-accept chrome — token field wired to login for MVP. */
export default function InvitePage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [msg, setMsg] = useState("");

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token.trim()) {
      setMsg("Enter an invite token.");
      return;
    }
    sessionStorage.setItem(INVITE_STORAGE_KEY, token.trim());
    setMsg("Invite stored. Continue to sign in.");
    router.push("/login");
  }

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-6 px-6 py-16">
        <Card>
          <CardHeader>
            <CardTitle>Accept invite</CardTitle>
            <CardDescription>Paste the invite token from your administrator.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="flex flex-col gap-3" onSubmit={onSubmit}>
              <label className="flex flex-col gap-1 text-sm">
                Invite token
                <Input
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="inv_…"
                  autoComplete="off"
                />
              </label>
              <Button type="submit">Continue</Button>
              {msg ? <p className="text-sm text-[rgb(var(--sift-text-muted))]">{msg}</p> : null}
              <Button variant="ghost" asChild>
                <Link href="/login">Back to sign in</Link>
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
      <SiteFooter />
    </div>
  );
}
