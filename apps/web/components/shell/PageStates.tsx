import { cn } from "@sift/ui";
import { Button, Skeleton } from "@sift/ui";

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {description ? (
          <p className="mt-1 text-sm text-[rgb(var(--sift-text-muted))]">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-dashed border-[rgb(var(--sift-border))] px-6 py-10 text-center">
      <p className="text-sm font-medium">{title}</p>
      <p className="mt-1 text-sm text-[rgb(var(--sift-text-muted))]">{body}</p>
      {action ? <div className="mt-4 flex justify-center">{action}</div> : null}
    </div>
  );
}

export function ErrorBanner({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-start justify-between gap-3 rounded-md border border-[rgb(var(--sift-danger))]/40 bg-[rgb(var(--sift-danger))]/10 px-3 py-2 text-sm text-[rgb(var(--sift-danger))]">
      <p>{message}</p>
      {onRetry ? (
        <Button type="button" variant="destructive" size="sm" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}

export function LoadingState({
  className,
  label: _label,
}: {
  className?: string;
  label?: string;
}) {
  return (
    <div className={cn("grid gap-3", className)}>
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-24 w-full" />
    </div>
  );
}
