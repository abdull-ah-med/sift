"use client";

import { useEffect, useRef, useState, type CSSProperties, type ElementType } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { SplitText as GSAPSplitText } from "gsap/SplitText";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(ScrollTrigger, GSAPSplitText, useGSAP);

export interface SplitTextProps {
  text: string;
  className?: string;
  delay?: number;
  duration?: number;
  ease?: string;
  splitType?: "chars" | "words" | "lines" | "words, chars";
  from?: gsap.TweenVars;
  to?: gsap.TweenVars;
  threshold?: number;
  rootMargin?: string;
  tag?: "h1" | "h2" | "h3" | "h4" | "h5" | "h6" | "p" | "span";
  textAlign?: CSSProperties["textAlign"];
}

/** React Bits SplitText. GSAP SplitText + ScrollTrigger, once. */
export default function SplitText({
  text,
  className = "",
  delay = 40,
  duration = 0.45,
  ease = "power2.out",
  splitType = "words",
  from = { opacity: 0, y: 12 },
  to = { opacity: 1, y: 0 },
  threshold = 0.1,
  rootMargin = "0px",
  tag = "p",
  textAlign = "left",
}: SplitTextProps) {
  const ref = useRef<HTMLElement>(null);
  const done = useRef(false);
  const [fontsLoaded, setFontsLoaded] = useState(false);

  useEffect(() => {
    if (document.fonts.status === "loaded") {
      setFontsLoaded(true);
      return;
    }
    document.fonts.ready.then(() => setFontsLoaded(true));
  }, []);

  useGSAP(
    () => {
      if (!ref.current || !text || !fontsLoaded || done.current) return;
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

      const el = ref.current as HTMLElement & { _rbsplitInstance?: GSAPSplitText };
      if (el._rbsplitInstance) {
        try {
          el._rbsplitInstance.revert();
        } catch {
          /* already reverted */
        }
        el._rbsplitInstance = undefined;
      }

      const startPct = (1 - threshold) * 100;
      const start = `top ${startPct}%`;

      const splitInstance = new GSAPSplitText(el, {
        type: splitType,
        smartWrap: true,
        autoSplit: splitType === "lines",
        linesClass: "split-line",
        wordsClass: "split-word",
        charsClass: "split-char",
        reduceWhiteSpace: false,
        onSplit: (self: GSAPSplitText) => {
          let targets: Element[] = [];
          if (splitType.includes("chars") && self.chars?.length) targets = self.chars;
          if (!targets.length && splitType.includes("words") && self.words.length) targets = self.words;
          if (!targets.length && splitType.includes("lines") && self.lines.length) targets = self.lines;
          if (!targets.length) targets = self.chars || self.words || self.lines;
          return gsap.fromTo(
            targets,
            { ...from },
            {
              ...to,
              duration,
              ease,
              stagger: delay / 1000,
              scrollTrigger: {
                trigger: el,
                start,
                once: true,
                fastScrollEnd: true,
              },
              onComplete: () => {
                done.current = true;
              },
              willChange: "transform, opacity",
              force3D: true,
            },
          );
        },
      });
      el._rbsplitInstance = splitInstance;
      return () => {
        ScrollTrigger.getAll().forEach((st) => {
          if (st.trigger === el) st.kill();
        });
        try {
          splitInstance.revert();
        } catch {
          /* already reverted */
        }
        el._rbsplitInstance = undefined;
      };
    },
    {
      dependencies: [text, delay, duration, ease, splitType, threshold, rootMargin, fontsLoaded],
      scope: ref,
    },
  );

  const Tag = (tag || "p") as ElementType;
  return (
    <Tag
      ref={ref}
      style={{ textAlign, wordWrap: "break-word" }}
      className={`split-parent inline-block whitespace-normal ${className}`}
    >
      {text}
    </Tag>
  );
}
