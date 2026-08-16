import { AppShell } from "@/components/shell/AppShell";

/** Authenticated app route group — product shell, not marketing chrome. */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
