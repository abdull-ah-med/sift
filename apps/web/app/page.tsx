import { Button } from "@sift/ui";
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex flex-col gap-6 py-8">
      <h1 className="text-3xl font-semibold tracking-tight">sift</h1>
      <p className="max-w-prose text-[rgb(var(--sift-text-muted))]">
        Privacy-first document intelligence. Authenticate, manage collections, and upload
        documents.
      </p>
      <div className="flex gap-3">
        <Button asChild>
          <Link href="/login">Sign in</Link>
        </Button>
        <Button variant="secondary" asChild>
          <Link href="/collections">Collections</Link>
        </Button>
      </div>
    </div>
  );
}
