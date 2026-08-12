"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { ReactLenis, type LenisRef } from "lenis/react";
import "lenis/dist/lenis.css";

const MARKETING_PATHS = new Set(["/", "/privacy", "/terms", "/login", "/signup", "/invite"]);

function isMarketingPath(pathname: string): boolean {
  if (MARKETING_PATHS.has(pathname)) {
    return true;
  }
  return ["/login", "/signup", "/invite", "/privacy", "/terms"].some((prefix) =>
    pathname.startsWith(`${prefix}/`),
  );
}

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

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
 * The wrapper is pathname-stable (no remount). Reduced-motion users get
 * `lenis.stop()` so scrolling stays native.
 */
export function LenisProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const reduced = usePrefersReducedMotion();
  const lenisRef = useRef<LenisRef>(null);
  const marketing = isMarketingPath(pathname);

  useEffect(() => {
    const lenis = lenisRef.current?.lenis;
    if (!lenis) {
      return;
    }
    if (reduced) {
      lenis.stop();
    } else {
      lenis.start();
    }
  }, [reduced, marketing]);

  if (!marketing) {
    return children;
  }

  return (
    <ReactLenis root ref={lenisRef} options={{ autoRaf: true, lerp: 0.1 }}>
      {children}
    </ReactLenis>
  );
}
