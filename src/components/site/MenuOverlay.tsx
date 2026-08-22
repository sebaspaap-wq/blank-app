"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useSite } from "./SiteProvider";
import { useLockBodyScroll } from "@/hooks/useLockBodyScroll";
import { IMAGES } from "@/lib/images";

const PRIMARY = [
  { label: "COLLECTION", href: "/collection", image: IMAGES.sandTerrace },
  { label: "ABOUT CAVÁ", href: "/about", image: IMAGES.ivoryInterior },
  { label: "JOURNAL", href: "/journal", image: IMAGES.cacaoSunset },
  { label: "CONTACT", href: "/contact", image: IMAGES.cacaoPool },
];

const SECONDARY = [
  { label: "Shipping", href: "/service/shipping" },
  { label: "Returns", href: "/service/returns" },
  { label: "Size Guide", href: "/service/size-guide" },
  { label: "Care", href: "/service/care" },
];

const EASE = [0.22, 1, 0.36, 1] as const;

export default function MenuOverlay() {
  const { overlay, close } = useSite();
  const isOpen = overlay === "menu";
  const reduced = useReducedMotion();
  const [hovered, setHovered] = useState<number | null>(null);

  useLockBodyScroll(isOpen);

  useEffect(() => {
    if (!isOpen) {
      setHovered(null);
      return;
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, close]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          id="cava-menu"
          className="on-dark fixed inset-0 z-[80] bg-noir text-ivory"
          initial={reduced ? { opacity: 0 } : { clipPath: "inset(0 0 100% 0)" }}
          animate={reduced ? { opacity: 1 } : { clipPath: "inset(0 0 0% 0)" }}
          exit={reduced ? { opacity: 0 } : { clipPath: "inset(0 0 100% 0)" }}
          transition={{ duration: reduced ? 0.2 : 0.9, ease: EASE }}
          onClick={(event) => {
            if (event.target === event.currentTarget) close();
          }}
        >
          {/* hover preview */}
          <div className="pointer-events-none absolute inset-y-0 right-0 hidden w-[38%] lg:block">
            {PRIMARY.map((item, index) => (
              <div
                key={item.href}
                className="absolute inset-0"
                style={{
                  opacity: hovered === index ? 0.42 : 0,
                  transform: `scale(${hovered === index ? 1 : 1.06})`,
                  transition: "opacity 1.1s var(--ease), transform 1.6s var(--ease)",
                }}
              >
                <Image
                  src={item.image.src}
                  alt=""
                  fill
                  sizes="38vw"
                  className="object-cover"
                  style={{
                    maskImage: "linear-gradient(to right, transparent, #000 45%)",
                    WebkitMaskImage: "linear-gradient(to right, transparent, #000 45%)",
                  }}
                />
              </div>
            ))}
          </div>

          <div
            className="relative flex h-full flex-col justify-between gutter pb-10 pt-[calc(var(--nav-h)+3rem)] md:pb-16"
            onClick={(event) => {
              if (event.target === event.currentTarget) close();
            }}
          >
            <nav aria-label="Menu" className="flex flex-1 items-end pb-14 md:flex-none md:items-start md:pb-0">
              <ul className="w-full">
                {PRIMARY.map((item, index) => (
                  <motion.li
                    key={item.href}
                    initial={reduced ? false : { y: "110%", opacity: 0 }}
                    animate={{ y: "0%", opacity: 1 }}
                    transition={{
                      duration: 1,
                      ease: EASE,
                      delay: reduced ? 0 : 0.22 + index * 0.075,
                    }}
                    onMouseEnter={() => setHovered(index)}
                    onMouseLeave={() => setHovered(null)}
                  >
                    <Link
                      href={item.href}
                      onClick={close}
                      className="group/menu flex items-baseline gap-5 py-1.5 md:gap-10 md:py-2"
                    >
                      <span className="eyebrow w-6 shrink-0 opacity-35 md:w-10">
                        0{index + 1}
                      </span>
                      <span
                        className="font-serif-display block text-[clamp(2.5rem,10vw,7rem)] leading-[1.08] transition-transform duration-700 group-hover/menu:translate-x-2 md:leading-[1.02]"
                        style={{ transitionTimingFunction: "var(--ease)" }}
                      >
                        {item.label}
                      </span>
                    </Link>
                  </motion.li>
                ))}
              </ul>
            </nav>

            <motion.div
              initial={reduced ? false : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.1, ease: EASE, delay: reduced ? 0 : 0.6 }}
              className="flex flex-col gap-8 border-t border-[rgba(245,242,235,0.16)] pt-8 md:flex-row md:items-end md:justify-between"
            >
              <ul className="flex flex-wrap gap-x-8 gap-y-3">
                {SECONDARY.map((item) => (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={close}
                      className="nav-label link-grow opacity-60 transition-opacity duration-500 hover:opacity-100"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
              <p className="eyebrow opacity-40">THE ART OF SLOW LIVING</p>
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
