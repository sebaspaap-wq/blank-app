"use client";

import { useEffect } from "react";

let lockCount = 0;

/** Locks page scroll while any overlay is open, without layout shift. */
export function useLockBodyScroll(active: boolean) {
  useEffect(() => {
    if (!active) return;

    const body = document.body;
    const scrollbar = window.innerWidth - document.documentElement.clientWidth;

    lockCount += 1;
    body.dataset.locked = "true";
    if (scrollbar > 0) body.style.paddingRight = `${scrollbar}px`;

    return () => {
      lockCount = Math.max(0, lockCount - 1);
      if (lockCount === 0) {
        delete body.dataset.locked;
        body.style.paddingRight = "";
      }
    };
  }, [active]);
}
