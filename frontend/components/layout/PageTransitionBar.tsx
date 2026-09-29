"use client";

import { useEffect, useRef } from "react";
import { usePathname, useSearchParams } from "next/navigation";

/**
 * Shows a thin amber progress bar at the top of the page during route transitions.
 * This gives instant visual feedback so users know a click registered even when
 * the new page is still loading.
 */
export default function PageTransitionBar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const barRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    const bar = barRef.current;
    if (!bar) return;

    // Route changed — show "done" flash then hide
    bar.classList.remove("loading");
    bar.classList.add("done");

    timerRef.current = setTimeout(() => {
      bar.classList.remove("done");
      bar.style.opacity = "1";
    }, 350);

    return () => clearTimeout(timerRef.current);
  }, [pathname, searchParams]);

  // Listen for link clicks to immediately show loading state
  useEffect(() => {
    const bar = barRef.current;
    if (!bar) return;

    const handleClick = (e: MouseEvent) => {
      const target = (e.target as HTMLElement).closest("a");
      if (!target) return;
      const href = target.getAttribute("href");
      // Only trigger for internal links that aren't current page
      if (href && href.startsWith("/") && href !== window.location.pathname) {
        bar.classList.remove("done");
        bar.style.opacity = "1";
        bar.classList.add("loading");
      }
    };

    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, []);

  return (
    <div
      ref={barRef}
      id="page-loading-bar"
      aria-hidden="true"
    />
  );
}
