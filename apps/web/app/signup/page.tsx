import Link from "next/link";
import { Button } from "@sift/ui";
import { AuthShell } from "@/components/auth/AuthShell";

/** Signup chrome — OIDC entry shares the login flow; no fake email register. */
export default function SignupPage() {
  return (
    <AuthShell
      title="Get started"
      description="Create a sift account via Zitadel, then open your first collection."
    >
      <Button asChild>
        <Link href="/login">Continue to sign in</Link>
      </Button>
      <Button variant="secondary" asChild>
        <Link href="/invite">Have an invite?</Link>
      </Button>
    </AuthShell>
  );
}
