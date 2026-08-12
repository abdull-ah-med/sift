"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button, Input, Label } from "@sift/ui";
import { AuthShell } from "@/components/auth/AuthShell";
import { INVITE_STORAGE_KEY } from "@/lib/invite";

/** Invite-accept chrome — token field wired to login. */
export default function InvitePage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [err, setErr] = useState("");

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token.trim()) {
      setErr("Enter the invite token from your administrator.");
      return;
    }
    sessionStorage.setItem(INVITE_STORAGE_KEY, token.trim());
    toast.success("Invite stored. Continue to sign in.");
    router.push("/login");
  }

  return (
    <AuthShell title="Accept invite" description="Paste the invite token from your administrator.">
      <form className="flex flex-col gap-3" onSubmit={onSubmit}>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="invite-token">Invite token</Label>
          <Input
            id="invite-token"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="inv_…"
            autoComplete="off"
          />
        </div>
        {err ? <p className="text-sm text-[rgb(var(--sift-danger))]">{err}</p> : null}
        <Button type="submit">Continue</Button>
        <Button variant="ghost" asChild>
          <Link href="/login">Back to sign in</Link>
        </Button>
      </form>
    </AuthShell>
  );
}
