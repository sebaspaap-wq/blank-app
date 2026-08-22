"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useSite } from "./SiteProvider";
import { useLockBodyScroll } from "@/hooks/useLockBodyScroll";
import { PRODUCTS, formatPrice } from "@/lib/products";

const EASE = [0.22, 1, 0.36, 1] as const;
const SUGGESTIONS = ["Signature Robe", "Sand", "Ivory", "Cacao", "Gifting"];

export default function SearchOverlay() {
  const { overlay, close } = useSite();
  const isOpen = overlay === "search";
  const reduced = useReducedMotion();
  const [query, setQuery] = useState("");
  const input = useRef<HTMLInputElement>(null);

  useLockBodyScroll(isOpen);

  useEffect(() => {
    if (!isOpen) {
      setQuery("");
      return;
    }
    const id = window.setTimeout(() => input.current?.focus(), 520);
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.clearTimeout(id);
      window.removeEventListener("keydown", onKey);
    };
  }, [isOpen, close]);

  const results = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return PRODUCTS;
    return PRODUCTS.filter((product) =>
      [product.colour, product.name, product.subtitle, product.slug]
        .join(" ")
        .toLowerCase()
        .includes(term)
    );
  }, [query]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-[85] bg-ivory"
          initial={reduced ? { opacity: 0 } : { clipPath: "inset(0 0 100% 0)" }}
          animate={reduced ? { opacity: 1 } : { clipPath: "inset(0 0 0% 0)" }}
          exit={reduced ? { opacity: 0 } : { clipPath: "inset(0 0 100% 0)" }}
          transition={{ duration: reduced ? 0.2 : 0.8, ease: EASE }}
          role="dialog"
          aria-modal
          aria-label="Search"
        >
          <div className="flex h-full flex-col gutter pt-[calc(var(--nav-h)+2.5rem)]">
            <div className="flex items-center justify-between">
              <p className="eyebrow opacity-45">SEARCH</p>
              <button type="button" onClick={close} className="nav-label link-grow cursor-pointer">
                CLOSE
              </button>
            </div>

            <div className="mt-10 border-b border-[var(--hairline)] pb-5 transition-colors duration-700 focus-within:border-[rgba(8,8,7,0.6)]">
              <input
                ref={input}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="What are you looking for?"
                aria-label="Search CAVÁ"
                className="font-serif-display w-full bg-transparent text-[clamp(1.75rem,5vw,3.5rem)] outline-none placeholder:opacity-25"
              />
            </div>

            <div className="mt-6 flex flex-wrap gap-x-7 gap-y-3">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => setQuery(suggestion)}
                  className="nav-label link-grow cursor-pointer opacity-45 transition-opacity duration-500 hover:opacity-100"
                >
                  {suggestion}
                </button>
              ))}
            </div>

            <div className="no-scrollbar mt-12 flex-1 overflow-y-auto pb-16">
              {results.length === 0 ? (
                <p className="body-copy opacity-50">
                  Nothing matches “{query}”. The CAVÁ collection is intentionally small.
                </p>
              ) : (
                <ul className="grid grid-cols-2 gap-x-4 gap-y-10 md:grid-cols-3 md:gap-x-8">
                  {results.map((product, index) => (
                    <motion.li
                      key={product.slug}
                      initial={reduced ? false : { opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.8, ease: EASE, delay: 0.25 + index * 0.06 }}
                    >
                      <Link href={`/collection/${product.slug}`} onClick={close} className="group/card block">
                        <div className="media media-zoom relative aspect-[3/4]" data-cursor="view">
                          <Image
                            src={product.card.src}
                            alt={product.card.alt}
                            fill
                            sizes="(max-width: 768px) 45vw, 30vw"
                            placeholder="blur"
                            blurDataURL={product.card.blurDataURL}
                            className={`object-cover ${product.cardPosition}`}
                          />
                        </div>
                        <p className="nav-label mt-5">{product.colour}</p>
                        <p className="body-copy mt-1 opacity-55">{product.name}</p>
                        <p className="price mt-2">{formatPrice(product.price)}</p>
                      </Link>
                    </motion.li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
