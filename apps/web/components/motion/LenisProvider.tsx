"use client";

import { useEffect, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { ReactLenis, useLenis } from "lenis/react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import "lenis/dist/lenis.css";

gsap.registerPlugin(ScrollTrigger);

function LenisScrollTriggerBridge() {
  useLenis(() => {
    ScrollTrigger.update();
  });
  return null;
}

const MARKETING_PATHS = new Set([
  "/",
  "/privacy",
  "/terms",
  "/ai",
  "/data",
  "/mission",
  "/login",
  "/signup",
  "/invite",
]);

function isMarketingPath(pathname: string): boolean {
  if (MARKETING_PATHS.has(pathname)) {
    return true;
  }
  return ["/login", "/signup", "/invite", "/privacy", "/terms", "/ai", "/data", "/mission"].some(
    (prefix) => pathname.startsWith(`${prefix}/`),
  );
}

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(true);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => {
      setReduced(media.matches);
    };
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  return reduced;
}

/**
 * Smooth-scrolls public marketing/auth routes with Lenis.
 * Reduced-motion users keep native scroll — Lenis is not mounted, because
 * `lenis.stop()` applies `overflow: clip` and freezes the page.
 */
export function LenisProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const reduced = usePrefersReducedMotion();
  const marketing = isMarketingPath(pathname);

  if (!marketing || reduced) {
    return children;
  }

  return (
    <ReactLenis root options={{ autoRaf: true, lerp: 0.1, respectReducedMotion: true }}>
      <LenisScrollTriggerBridge />
      {children}
    </ReactLenis>
  );
}
