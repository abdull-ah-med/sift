"use client";

import * as React from "react";
import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

interface FadeContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  duration?: number;
  ease?: string;
  delay?: number;
  threshold?: number;
  initialOpacity?: number;
}

/** React Bits FadeContent. GSAP + ScrollTrigger, once. */
export default function FadeContent({
  children,
  duration = 0.4,
  ease = "power2.out",
  delay = 0,
  threshold = 0.1,
  initialOpacity = 0,
  className = "",
  ...props
}: FadeContentProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const seconds = reduced ? 0.2 : duration > 10 ? duration / 1000 : duration;
    const delayS = reduced ? 0 : delay > 10 ? delay / 1000 : delay;
    const startPct = (1 - threshold) * 100;
    const fromOpacity = reduced ? 0.35 : initialOpacity;

    gsap.set(el, { autoAlpha: fromOpacity });

    const tl = gsap.timeline({ paused: true, delay: delayS });
    tl.to(el, { autoAlpha: 1, duration: seconds, ease });

    const st = ScrollTrigger.create({
      trigger: el,
      start: `top ${startPct}%`,
      once: true,
      onEnter: () => tl.play(),
    });
    const rect = el.getBoundingClientRect();
    const vh = window.innerHeight || 0;
    const alreadyInView = rect.top < vh * (startPct / 100) && rect.bottom > 0;
    if (threshold === 0 || alreadyInView) {
      tl.play();
    }

    return () => {
      st.kill();
      tl.kill();
      gsap.killTweensOf(el);
    };
  }, [duration, ease, delay, threshold, initialOpacity]);

  return (
    <div ref={ref} className={`opacity-0 ${className}`} {...props}>
      {children}
    </div>
  );
}
