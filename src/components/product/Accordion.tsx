"use client";

import { useId, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

const EASE = [0.22, 1, 0.36, 1] as const;

type Props = {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
};

export default function Accordion({ title, children, defaultOpen = false }: Props) {
  const [open, setOpen] = useState(defaultOpen);
  const reduced = useReducedMotion();
  const id = useId();

  return (
    <div className="border-b border-[var(--hairline)]">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-controls={id}
        className="flex w-full cursor-pointer items-center justify-between py-5 text-left"
      >
        <span className="nav-label">{title}</span>
        <span className="relative block h-3 w-3" aria-hidden>
          <span className="absolute left-0 top-1/2 h-[1px] w-3 -translate-y-1/2 bg-current" />
          <span
            className="absolute left-1/2 top-0 h-3 w-[1px] -translate-x-1/2 bg-current transition-transform duration-700"
            style={{
              transform: `translateX(-50%) scaleY(${open ? 0 : 1})`,
              transitionTimingFunction: "var(--ease)",
            }}
          />
        </span>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            id={id}
            initial={reduced ? { opacity: 0 } : { height: 0, opacity: 0 }}
            animate={reduced ? { opacity: 1 } : { height: "auto", opacity: 1 }}
            exit={reduced ? { opacity: 0 } : { height: 0, opacity: 0 }}
            transition={{ duration: 0.55, ease: EASE }}
            className="overflow-hidden"
          >
            <div className="pb-7 pr-6">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
