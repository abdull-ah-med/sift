"use client";

import { Button } from "@sift/ui";
import { PageHeader } from "@/components/shell/PageStates";

export default function AppError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <>
      <PageHeader title="This view failed to load" description="The page hit an unexpected error." />
      <p className="mb-4 text-sm text-[rgb(var(--sift-text-muted))]">
        Retry this view. If it keeps failing, sign in again or open Home.
      </p>
      <Button type="button" onClick={() => reset()}>
        Retry
      </Button>
    </>
  );
}
