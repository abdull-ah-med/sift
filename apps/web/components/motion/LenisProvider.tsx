"use client";

import { useEffect, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { ReactLenis, useLenis } from "lenis/react";
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

function LenisReducedMotionGate({ reduced }: { reduced: boolean }) {
  const lenis = useLenis();

  useEffect(() => {
    if (!lenis) {
      return;
    }
    if (reduced) {
      lenis.stop();
    } else {
      lenis.start();
    }
  }, [lenis, reduced]);

  return null;
}

/**
 * Smooth-scrolls public marketing/auth routes with Lenis.
 * The wrapper is pathname-stable (no remount). Reduced-motion users get
 * `lenis.stop()` once the instance exists.
 */
export function LenisProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const reduced = usePrefersReducedMotion();
  const marketing = isMarketingPath(pathname);

  if (!marketing) {
    return children;
  }

  return (
    <ReactLenis root options={{ autoRaf: true, lerp: 0.1 }}>
      <LenisReducedMotionGate reduced={reduced} />
      {children}
    </ReactLenis>
  );
}
