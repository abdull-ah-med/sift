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

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      gsap.set(el, { x: 0, y: 0, opacity: 1, visibility: "visible" });
      return;
    }

    const axis = direction === "horizontal" ? "x" : "y";
    const offset = reverse ? -distance : distance;
    const startPct = (1 - threshold) * 100;

    gsap.set(el, { [axis]: offset, opacity: 0, visibility: "visible" });

    const tl = gsap.timeline({ paused: true, delay });
    tl.to(el, { [axis]: 0, opacity: 1, duration, ease });

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
    <div ref={ref} className={`opacity-0 motion-reduce:opacity-100 ${className}`} {...props}>
      {children}
    </div>
  );
}
