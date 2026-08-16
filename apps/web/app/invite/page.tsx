"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button, Field, FieldError, FieldGroup, FieldLabel, Input } from "@sift/ui";
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
      <form className="flex flex-col gap-4" onSubmit={onSubmit}>
        <FieldGroup>
          <Field data-invalid={err ? true : undefined}>
            <FieldLabel htmlFor="invite-token">Invite token</FieldLabel>
            <Input
              id="invite-token"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="inv_…"
              autoComplete="off"
              aria-invalid={Boolean(err)}
            />
            {err ? <FieldError>{err}</FieldError> : null}
          </Field>
        </FieldGroup>
        <Button type="submit" className="w-full">
          Continue
        </Button>
        <Button variant="ghost" asChild className="w-full">
          <Link href="/login">Back to sign in</Link>
        </Button>
      </form>
    </AuthShell>
  );
}
