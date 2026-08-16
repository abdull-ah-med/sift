"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLenis } from "lenis/react";
import { cn } from "@sift/ui";
import { useEffect, useState, type ComponentProps, type MouseEvent } from "react";

/** Clears the fixed pill nav (`pt-4` + `h-16`) plus a little air. */
export const HEADER_SCROLL_OFFSET = -128;

const NAV =
  "px-3 py-2 text-sm font-medium text-[rgb(var(--sift-text-muted))] underline-offset-4 decoration-[rgb(var(--sift-text))] transition-colors duration-150 ease-[var(--ease-out)] [@media(hover:hover)_and_(pointer:fine)]:hover:text-[rgb(var(--sift-text))] [@media(hover:hover)_and_(pointer:fine)]:hover:underline data-[active=true]:text-[rgb(var(--sift-text))] data-[active=true]:underline";

const TEXT =
  "relative inline-flex text-sm text-[rgb(var(--sift-text-muted))] transition-colors duration-150 ease-[var(--ease-out)] after:pointer-events-none after:absolute after:inset-x-0 after:-bottom-0.5 after:h-px after:origin-left after:scale-x-0 after:bg-current after:transition-transform after:duration-150 after:ease-[var(--ease-out)] motion-reduce:after:transition-none [@media(hover:hover)_and_(pointer:fine)]:hover:text-[rgb(var(--sift-text))] [@media(hover:hover)_and_(pointer:fine)]:hover:after:scale-x-100";

function hashFromHref(href: string): string | null {
  if (href.startsWith("#")) {
    return href.slice(1) || null;
  }
  if (href.startsWith("/#")) {
    return href.slice(2) || null;
  }
  return null;
}

/** Lenis-aware in-page scroll; native smooth scroll when Lenis is not mounted. */
export function scrollToHash(
  id: string,
  lenis: ReturnType<typeof useLenis> | undefined,
): void {
  const el = document.getElementById(id);
  if (!el) {
    return;
  }
  if (lenis) {
    lenis.scrollTo(el, { offset: HEADER_SCROLL_OFFSET, duration: 1.05 });
    return;
  }
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
}

type HashLinkProps = ComponentProps<typeof Link> & {
  variant?: "nav" | "text";
};

/**
 * Next Link with watermelon-style hover (color + origin-left underline) and
 * Lenis hash scrolling so in-page nav does not jump under the fixed header.
 */
export function HashLink({
  href,
  className,
  variant = "text",
  onClick,
  children,
  ...rest
}: HashLinkProps) {
  const pathname = usePathname();
  const lenis = useLenis();
  const hrefStr = typeof href === "string" ? href : "";
  const targetHash = hrefStr ? hashFromHref(hrefStr) : null;
  const [hash, setHash] = useState("");

  useEffect(() => {
    const sync = () => setHash(window.location.hash.replace(/^#/, ""));
    sync();
    window.addEventListener("hashchange", sync);
    window.addEventListener("popstate", sync);
    return () => {
      window.removeEventListener("hashchange", sync);
      window.removeEventListener("popstate", sync);
    };
  }, []);

  const active =
    variant === "nav" &&
    (targetHash
      ? pathname === "/" && hash === targetHash
      : hrefStr !== "" &&
        hrefStr !== "/" &&
        (pathname === hrefStr || pathname.startsWith(`${hrefStr}/`)));

  function handleClick(e: MouseEvent<HTMLAnchorElement>) {
    onClick?.(e);
    if (e.defaultPrevented || !targetHash) {
      return;
    }
    if (pathname !== "/") {
      return;
    }
    e.preventDefault();
    scrollToHash(targetHash, lenis);
    window.history.replaceState(null, "", `/#${targetHash}`);
    setHash(targetHash);
  }

  return (
    <Link
      href={href}
      onClick={handleClick}
      data-active={active || undefined}
      aria-current={active ? "page" : undefined}
      className={cn(variant === "nav" ? NAV : TEXT, className)}
      {...rest}
    >
      {children}
    </Link>
  );
}
