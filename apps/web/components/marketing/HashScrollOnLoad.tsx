"use client";

import { useEffect } from "react";
import { useLenis } from "lenis/react";
import { scrollToHash } from "@/components/marketing/HashLink";

/** After a cross-route navigation to `/#id`, scroll with the same nav offset. */
export function HashScrollOnLoad() {
  const lenis = useLenis();

  useEffect(() => {
    const id = window.location.hash.replace(/^#/, "");
    if (!id) {
      return;
    }
    const t = window.setTimeout(() => {
      scrollToHash(id, lenis);
    }, 80);
    return () => window.clearTimeout(t);
  }, [lenis]);

  return null;
}
