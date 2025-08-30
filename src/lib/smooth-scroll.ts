import Lenis from 'lenis';

let lenis: Lenis | null = null;

// Check if device is mobile
const isMobile = () => {
  if (typeof window === "undefined") return false;
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
         window.innerWidth <= 768;
};

export const initSmoothScroll = () => {
  if (typeof window === "undefined") return;

  // Skip Lenis on mobile devices to prevent jittery scrolling
  if (isMobile()) {
    return null;
  }

  // Initialize Lenis only on desktop
  lenis = new Lenis({
    duration: 1.2,
    easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
  });

  // RAF loop for Lenis
  function raf(time: number) {
    lenis?.raf(time);
    requestAnimationFrame(raf);
  }
  requestAnimationFrame(raf);

  return lenis;
};

export const scrollTo = (target: string | number, options?: object) => {
  if (typeof window === "undefined") return;

  // Use native scrolling on mobile for better performance
  if (isMobile() || !lenis) {
    if (typeof target === 'string' && target.startsWith('#')) {
      const element = document.getElementById(target.slice(1));
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
    return;
  }

  // Use Lenis on desktop
  try {
    lenis.scrollTo(target, {
      duration: 1.5,
      easing: (t: number) => 1 - Math.pow(1 - t, 3),
      ...options,
    });
  } catch {
    // Fallback to native scroll
    if (typeof target === 'string' && target.startsWith('#')) {
      const element = document.getElementById(target.slice(1));
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  }
};

export const destroySmoothScroll = () => {
  if (lenis) {
    lenis.destroy();
    lenis = null;
  }
};
