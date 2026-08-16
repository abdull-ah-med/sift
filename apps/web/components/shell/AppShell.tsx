"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  Button,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  Separator,
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
  Skeleton,
} from "@sift/ui";
import { getAccessToken, getApiKey } from "@/lib/api";
import { consumeStoredInvite, INVITE_STORAGE_KEY } from "@/lib/invite";
import { CommandPalette } from "./CommandPalette";

const NAV = [
  { href: "/home", label: "Home" },
  { href: "/collections", label: "Collections" },
  { href: "/tenants", label: "Tenants" },
  { href: "/settings/api-keys", label: "Settings" },
] as const;

function crumb(pathname: string): string {
  if (pathname.startsWith("/home")) return "Home";
  if (pathname.startsWith("/collections")) return "Collections";
  if (pathname.startsWith("/tenants")) return "Tenants";
  if (pathname.startsWith("/settings")) return "Settings";
  if (pathname.startsWith("/auth/callback")) return "Sign in";
  return "Workspace";
}

function signOut() {
  localStorage.removeItem("sift_access_token");
  localStorage.removeItem("sift_api_key");
  sessionStorage.removeItem(INVITE_STORAGE_KEY);
}

/** Authenticated product chrome — shadcn sidebar-07. */
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [cmdOpen, setCmdOpen] = useState(false);
  const [ready, setReady] = useState(false);
  const isCallback = pathname.startsWith("/auth/callback");

  useEffect(() => {
    if (isCallback) {
      setReady(true);
      return;
    }
    if (!getAccessToken() && !getApiKey()) {
      router.replace("/login");
      return;
    }
    setReady(true);
    void consumeStoredInvite();
  }, [isCallback, router]);

  if (!ready) {
    return (
      <div className="flex min-h-svh items-center justify-center bg-[rgb(var(--sift-bg))]">
        <Skeleton className="h-8 w-48" />
      </div>
    );
  }

  return (
    <SidebarProvider>
      <Sidebar collapsible="icon" variant="inset">
        <SidebarHeader>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton asChild>
                <Link href="/home" className="font-semibold">
                  sift
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Workspace</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {NAV.map((item) => {
                  const active =
                    pathname === item.href || pathname.startsWith(`${item.href}/`);
                  return (
                    <SidebarMenuItem key={item.href}>
                      <SidebarMenuButton asChild isActive={active} tooltip={item.label}>
                        <Link href={item.href}>{item.label}</Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
        <SidebarFooter>
          <SidebarMenu>
            <SidebarMenuItem>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <SidebarMenuButton>Account</SidebarMenuButton>
                </DropdownMenuTrigger>
                <DropdownMenuContent side="top" align="start" className="w-48">
                  <DropdownMenuItem asChild>
                    <Link href="/login">Sign in</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => {
                      signOut();
                      router.replace("/login");
                    }}
                  >
                    Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarFooter>
      </Sidebar>
      <SidebarInset>
        <header className="flex h-12 shrink-0 items-center gap-2 border-b border-[rgb(var(--sift-border))] px-3">
          <SidebarTrigger />
          <Separator orientation="vertical" className="h-4" />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage>{crumb(pathname)}</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <div className="ml-auto">
            <Button type="button" variant="secondary" size="sm" onClick={() => setCmdOpen(true)}>
              Search… <kbd className="ml-2 font-mono text-[10px] opacity-70">⌘K</kbd>
            </Button>
          </div>
        </header>
        <div
          id="main"
          data-lenis-prevent
          className="sift-app-main flex-1 overflow-auto px-6 py-6"
        >
          {children}
        </div>
      </SidebarInset>
      <CommandPalette open={cmdOpen} onOpenChange={setCmdOpen} />
    </SidebarProvider>
  );
}
