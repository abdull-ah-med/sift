"use client";

import { useEffect, useRef, type HTMLAttributes, type ReactNode } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

interface AnimatedContentProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  distance?: number;
  direction?: "vertical" | "horizontal";
  reverse?: boolean;
  duration?: number;
  ease?: string;
  delay?: number;
  threshold?: number;
}

/** React Bits AnimatedContent. GSAP + ScrollTrigger, once. */
export default function AnimatedContent({
  children,
  distance = 12,
  direction = "vertical",
  reverse = false,
  duration = 0.4,
  ease = "power2.out",
  delay = 0,
  threshold = 0.1,
  className = "",
  ...props
}: AnimatedContentProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const axis = direction === "horizontal" ? "x" : "y";
    const travel = reduced ? Math.min(4, Math.abs(distance)) : distance;
    const offset = reverse ? -travel : travel;
    const startPct = (1 - threshold) * 100;
    const seconds = reduced ? 0.2 : duration;

    gsap.set(el, { [axis]: offset, opacity: 0, visibility: "visible" });

    const tl = gsap.timeline({ paused: true, delay: reduced ? 0 : delay });
    tl.to(el, { [axis]: 0, opacity: 1, duration: seconds, ease });

    const st = ScrollTrigger.create({
      trigger: el,
      start: `top ${startPct}%`,
      once: true,
      onEnter: () => tl.play(),
    });

    return () => {
      st.kill();
      tl.kill();
    };
  }, [distance, direction, reverse, duration, ease, delay, threshold]);

  return (
    <div ref={ref} className={`opacity-0 ${className}`} {...props}>
      {children}
    </div>
  );
}
