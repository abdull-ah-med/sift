"use client";

import Link from "next/link";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
  Badge,
  Button,
  cn,
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  Sheet,
  SheetContent,
  SheetDescription,
  SheetTitle,
  SheetTrigger,
} from "@sift/ui";
import {
  ArrowUpRight,
  FileUp,
  Menu,
  MessageSquareQuote,
  ScanLine,
  Search,
} from "lucide-react";
import FadeContent from "@/components/bits/FadeContent";
import { HashLink } from "@/components/marketing/HashLink";
import { LEGAL_LINKS } from "@/components/marketing/legal";

const CHIP =
  "h-7 gap-1.5 rounded-full px-3 text-xs text-[rgb(var(--sift-text-muted))]";

/** Watermelon navigation-5 structure, sift tokens and routes. */
export function SiteHeader() {
  return (
    <header className="fixed top-0 right-0 left-0 z-50">
      <div className="mx-auto flex items-center justify-center px-4 pt-4">
        <FadeContent
          delay={0}
          duration={0.4}
          threshold={0}
          className="w-full max-w-4xl md:max-w-6xl lg:max-w-7xl"
        >
        <div className="flex h-16 w-full items-center justify-between gap-2 rounded-full border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-text)_/_0.04)] pr-3 shadow-[inset_0_1px_0_0_rgb(238_238_238_/_0.06)] backdrop-blur-sm">
          <Link href="/" className="flex items-center gap-2 pr-6 pl-6">
            <span className="text-lg font-bold tracking-tight text-[rgb(var(--sift-text))]">
              sift
            </span>
          </Link>

          <div className="hidden lg:block">
            <NavigationMenu
              className={cn(
                "static",
                "[&>div:last-child]:inset-x-0 [&>div:last-child]:top-full [&>div:last-child]:w-full",
                "[&_[data-slot=navigation-menu-viewport]]:mx-auto [&_[data-slot=navigation-menu-viewport]]:mt-2 [&_[data-slot=navigation-menu-viewport]]:max-w-7xl [&_[data-slot=navigation-menu-viewport]]:ring-0",
                "[&_[data-slot=navigation-menu-viewport]]:rounded-[2.5rem] [&_[data-slot=navigation-menu-viewport]]:border [&_[data-slot=navigation-menu-viewport]]:border-[rgb(var(--sift-border-strong))]",
                "[&_[data-slot=navigation-menu-viewport]]:bg-[rgb(var(--sift-bg))] [&_[data-slot=navigation-menu-viewport]]:shadow-[inset_0_1px_0_0_rgb(238_238_238_/_0.06)]",
              )}
            >
              <NavigationMenuList className="gap-1">
                <NavigationMenuItem>
                  <NavigationMenuLink asChild>
                    <HashLink variant="nav" href="/#product">
                      Product
                    </HashLink>
                  </NavigationMenuLink>
                </NavigationMenuItem>

                <NavigationMenuItem>
                  <NavigationMenuLink asChild>
                    <HashLink variant="nav" href="/#how-it-works">
                      How it works
                    </HashLink>
                  </NavigationMenuLink>
                </NavigationMenuItem>

                <NavigationMenuItem>
                    <NavigationMenuTrigger className="h-auto rounded-none bg-transparent px-3 py-2 text-sm font-medium text-[rgb(var(--sift-text-muted))] underline-offset-4 decoration-[rgb(var(--sift-text))] transition-colors duration-150 ease-[var(--ease-out)] hover:bg-transparent hover:text-[rgb(var(--sift-text))] hover:underline focus:bg-transparent data-[state=open]:bg-transparent data-[state=open]:text-[rgb(var(--sift-text))] data-[state=open]:underline">
                    Surfaces
                  </NavigationMenuTrigger>
                  <NavigationMenuContent className="p-0 md:w-[min(64rem,calc(100vw-2rem))]">
                    <div className="grid w-[min(64rem,calc(100vw-2rem))] grid-cols-4 gap-6 divide-x divide-[rgb(var(--sift-border))] px-10 py-10">
                      <div className="flex flex-col px-2">
                        <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-xl border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-text)_/_0.04)]">
                          <MessageSquareQuote className="h-5 w-5 text-[rgb(var(--sift-text-muted))]" />
                        </div>
                        <h4 className="mb-1 text-sm font-medium text-[rgb(var(--sift-text))]">
                          Cited chat
                        </h4>
                        <p className="mb-3 text-sm tracking-tight text-[rgb(var(--sift-text-muted))]">
                          Answers that cite chunks, or refuse. Nothing reaches the thread without a
                          source.
                        </p>
                        <div className="flex flex-wrap gap-2">
                          <Button variant="outline" className={CHIP} asChild>
                            <Link href="/#product">
                              <FileUp className="h-3.5 w-3.5" />
                              Upload
                            </Link>
                          </Button>
                          <Button variant="outline" className={CHIP} asChild>
                            <Link href="/#product">
                              <ScanLine className="h-3.5 w-3.5" />
                              Review
                            </Link>
                          </Button>
                          <Button variant="outline" className={CHIP} asChild>
                            <Link href="/#product">
                              <Search className="h-3.5 w-3.5" />
                              Search
                            </Link>
                          </Button>
                        </div>
                      </div>

                      <div className="flex flex-col gap-3 pl-6">
                        <h4 className="mb-1 text-xs text-[rgb(var(--sift-text-muted))] uppercase">
                          Product
                        </h4>
                        <HashLink href="/#product" className="text-sm font-medium tracking-tight">
                          Upload
                        </HashLink>
                        <HashLink href="/#product" className="text-sm font-medium tracking-tight">
                          Review
                        </HashLink>
                        <HashLink href="/#product" className="text-sm font-medium tracking-tight">
                          Search
                        </HashLink>
                        <HashLink href="/#product" className="text-sm font-medium tracking-tight">
                          Cited chat
                        </HashLink>
                      </div>

                      <div className="flex flex-col gap-3 pl-6">
                        <h4 className="mb-1 text-xs text-[rgb(var(--sift-text-muted))] uppercase">
                          Resources
                        </h4>
                        {LEGAL_LINKS.map((link) => (
                          <HashLink
                            key={link.href}
                            href={link.href}
                            className="text-sm font-medium tracking-tight"
                          >
                            {link.label}
                          </HashLink>
                        ))}
                        <HashLink href="/collections" className="text-sm font-medium tracking-tight">
                          Collections
                        </HashLink>
                      </div>

                      <div className="flex flex-col pl-6">
                        <h4 className="mb-3 text-xs text-[rgb(var(--sift-text-muted))] uppercase">
                          Featured
                        </h4>
                        <Link
                          href="/signup"
                          className="group relative flex h-full flex-col justify-between overflow-hidden rounded-2xl border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-text)_/_0.04)] p-6 shadow-[inset_0_1px_0_0_rgb(238_238_238_/_0.06)]"
                        >
                          <div>
                            <Badge variant="outline" className="mb-3">
                              Get started
                            </Badge>
                            <h4 className="mb-2 text-sm font-semibold text-[rgb(var(--sift-text))]">
                              Open a collection
                            </h4>
                            <p className="text-sm tracking-tight text-[rgb(var(--sift-text-muted))]">
                              Put the contracts in. Keep the citations.
                            </p>
                          </div>
                          <div className="mt-4 flex items-center text-sm font-medium text-[rgb(var(--sift-accent))]">
                            Create workspace{" "}
                            <ArrowUpRight className="ml-1 size-4 transition-transform duration-150 ease-[var(--ease-out)] motion-safe:group-hover:translate-x-1" />
                          </div>
                        </Link>
                      </div>
                    </div>
                  </NavigationMenuContent>
                </NavigationMenuItem>

                <NavigationMenuItem>
                  <NavigationMenuLink asChild>
                    <HashLink variant="nav" href="/collections">
                      App
                    </HashLink>
                  </NavigationMenuLink>
                </NavigationMenuItem>
              </NavigationMenuList>
            </NavigationMenu>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild className="hidden rounded-full hover:bg-transparent md:inline-flex">
              <Link href="/login">Sign in</Link>
            </Button>
            <Button size="sm" asChild className="hidden rounded-full px-6 font-semibold md:inline-flex">
              <Link href="/signup">Get started</Link>
            </Button>

            <div className="lg:hidden">
              <Sheet>
                <SheetTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon-lg"
                    className="rounded-full hover:bg-transparent"
                    aria-label="Open menu"
                  >
                    <Menu className="size-5" />
                  </Button>
                </SheetTrigger>
                <SheetContent
                  side="right"
                  className="flex w-[300px] flex-col gap-6 bg-[rgb(var(--sift-bg))] p-6"
                >
                  <SheetTitle className="sr-only">Menu</SheetTitle>
                  <SheetDescription className="sr-only">Site navigation</SheetDescription>
                  <Link href="/" className="text-lg font-bold text-[rgb(var(--sift-text))]">
                    sift
                  </Link>

                  <div className="flex flex-col gap-4">
                    <HashLink href="/#product" className="text-base font-medium text-[rgb(var(--sift-text))]">
                      Product
                    </HashLink>
                    <HashLink href="/#how-it-works" className="text-base font-medium text-[rgb(var(--sift-text))]">
                      How it works
                    </HashLink>

                    <Accordion type="single" collapsible className="w-full">
                      <AccordionItem value="surfaces" className="border-none">
                        <AccordionTrigger className="justify-between py-0 text-base font-medium text-[rgb(var(--sift-text))]">
                          Surfaces
                        </AccordionTrigger>
                        <AccordionContent className="mt-1 ml-2 flex flex-col gap-3 border-l border-[rgb(var(--sift-border))] pb-0 pl-4 text-base font-medium">
                          <div className="flex flex-col gap-2 pt-4">
                            <span className="text-xs text-[rgb(var(--sift-text-muted))] uppercase">
                              Product
                            </span>
                            <HashLink href="/#product" className="text-sm font-medium tracking-tight">
                              Cited chat
                            </HashLink>
                            <HashLink href="/#product" className="text-sm font-medium tracking-tight">
                              Upload
                            </HashLink>
                            <HashLink href="/#product" className="text-sm font-medium tracking-tight">
                              Review
                            </HashLink>
                            <HashLink href="/#product" className="text-sm font-medium tracking-tight">
                              Search
                            </HashLink>
                          </div>
                          <div className="mt-2 flex flex-col gap-2">
                            <span className="text-xs text-[rgb(var(--sift-text-muted))] uppercase">
                              Resources
                            </span>
                            {LEGAL_LINKS.map((link) => (
                              <HashLink
                                key={link.href}
                                href={link.href}
                                className="text-sm font-medium tracking-tight"
                              >
                                {link.label}
                              </HashLink>
                            ))}
                            <HashLink href="/collections" className="text-sm font-medium tracking-tight">
                              Collections
                            </HashLink>
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>

                    <HashLink href="/collections" className="text-base font-medium text-[rgb(var(--sift-text))]">
                      App
                    </HashLink>
                    <HashLink href="/login" className="text-base font-medium text-[rgb(var(--sift-text))]">
                      Sign in
                    </HashLink>
                  </div>

                  <div className="mt-auto flex flex-col gap-3">
                    <Button asChild className="w-full rounded-full">
                      <Link href="/signup">Get started</Link>
                    </Button>
                  </div>
                </SheetContent>
              </Sheet>
            </div>
          </div>
        </div>
        </FadeContent>
      </div>
    </header>
  );
}
