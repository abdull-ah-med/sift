import type { Metadata } from "next";
import Link from "next/link";
import { Button } from "@sift/ui";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";

export const metadata: Metadata = {
  title: "Page not found",
};

export default function NotFound() {
  return (
    <div className="flex min-h-[100dvh] flex-col">
      <SiteHeader />
      <main id="main" className="sift-app-main mx-auto flex w-full max-w-lg flex-1 flex-col justify-center gap-6 px-6 py-24">
        <p className="text-sm text-[rgb(var(--sift-text-muted))]">404</p>
        <h1 className="text-2xl font-semibold tracking-tight">This page is not in the corpus.</h1>
        <p className="text-sm text-[rgb(var(--sift-text-muted))]">
          The URL does not match a public page. Return home or sign in to the app.
        </p>
        <div className="flex flex-wrap gap-3">
          <Button asChild>
            <Link href="/">Home</Link>
          </Button>
          <Button variant="secondary" asChild>
            <Link href="/login">Sign in</Link>
          </Button>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
