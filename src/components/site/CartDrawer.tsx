"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useSite } from "./SiteProvider";
import { useLockBodyScroll } from "@/hooks/useLockBodyScroll";
import { formatPrice } from "@/lib/products";

const EASE = [0.22, 1, 0.36, 1] as const;

export default function CartDrawer() {
  const { overlay, close, items, subtotal, setQuantity, remove } = useSite();
  const isOpen = overlay === "bag";
  const reduced = useReducedMotion();

  useLockBodyScroll(isOpen);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, close]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[95]" role="dialog" aria-modal aria-label="Your CAVÁ bag">
          <motion.button
            type="button"
            aria-label="Close bag"
            onClick={close}
            className="absolute inset-0 h-full w-full cursor-default bg-noir/45"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: EASE }}
          />

          <motion.aside
            className="absolute inset-y-0 right-0 flex w-full max-w-[30rem] flex-col bg-ivory"
            initial={reduced ? { opacity: 0 } : { x: "100%" }}
            animate={reduced ? { opacity: 1 } : { x: 0 }}
            exit={reduced ? { opacity: 0 } : { x: "100%" }}
            transition={{ duration: reduced ? 0.2 : 0.62, ease: EASE }}
          >
            <header className="flex items-center justify-between border-b border-[var(--hairline)] px-6 py-6 md:px-9">
              <h2 className="eyebrow">YOUR CAVÁ</h2>
              <button
                type="button"
                onClick={close}
                className="nav-label link-grow cursor-pointer"
              >
                CLOSE
              </button>
            </header>

            {items.length === 0 ? (
              <div className="flex flex-1 flex-col items-center justify-center gap-6 px-9 text-center">
                <p className="font-serif-display text-3xl">Your bag is empty.</p>
                <p className="body-copy max-w-[22rem] opacity-60">
                  Every CAVÁ piece is made in small quantities, in three enduring colours.
                </p>
                <Link href="/collection" onClick={close} className="link-line nav-label mt-2">
                  <span>DISCOVER THE COLLECTION</span>
                  <span aria-hidden className="arrow">→</span>
                </Link>
              </div>
            ) : (
              <>
                <ul className="no-scrollbar flex-1 overflow-y-auto px-6 md:px-9">
                  <AnimatePresence initial={false}>
                    {items.map((item) => (
                      <motion.li
                        key={item.id}
                        layout
                        initial={{ opacity: 0, y: 14 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, height: 0, marginTop: 0, marginBottom: 0 }}
                        transition={{ duration: 0.5, ease: EASE }}
                        className="flex gap-5 overflow-hidden border-b border-[var(--hairline)] py-6"
                      >
                        <Link
                          href={`/collection/${item.slug}`}
                          onClick={close}
                          className="media relative block h-[8.5rem] w-[6.5rem] shrink-0"
                        >
                          <Image
                            src={item.image}
                            alt={`${item.name} — ${item.colour}`}
                            fill
                            sizes="120px"
                            placeholder="blur"
                            blurDataURL={item.blurDataURL}
                            className="object-cover"
                          />
                        </Link>

                        <div className="flex flex-1 flex-col justify-between py-1">
                          <div>
                            <p className="font-serif-display text-lg">{item.name}</p>
                            <p className="nav-label mt-2 opacity-55">
                              {item.colour} · {item.size}
                            </p>
                          </div>

                          <div className="flex items-end justify-between">
                            <div className="flex items-center gap-4 border border-[var(--hairline)] px-3 py-1.5">
                              <button
                                type="button"
                                aria-label="Decrease quantity"
                                onClick={() => setQuantity(item.id, item.quantity - 1)}
                                className="cursor-pointer text-xs opacity-60 transition-opacity duration-300 hover:opacity-100"
                              >
                                −
                              </button>
                              <span className="price w-4 text-center">{item.quantity}</span>
                              <button
                                type="button"
                                aria-label="Increase quantity"
                                onClick={() => setQuantity(item.id, item.quantity + 1)}
                                className="cursor-pointer text-xs opacity-60 transition-opacity duration-300 hover:opacity-100"
                              >
                                +
                              </button>
                            </div>
                            <span className="price">{formatPrice(item.price * item.quantity)}</span>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={() => remove(item.id)}
                          className="eyebrow h-fit cursor-pointer opacity-35 transition-opacity duration-500 hover:opacity-90"
                          aria-label={`Remove ${item.name} ${item.colour} ${item.size}`}
                        >
                          ✕
                        </button>
                      </motion.li>
                    ))}
                  </AnimatePresence>
                </ul>

                <footer className="border-t border-[var(--hairline)] px-6 py-7 md:px-9">
                  <div className="flex items-baseline justify-between">
                    <span className="nav-label opacity-55">SUBTOTAL</span>
                    <span className="price text-base">{formatPrice(subtotal)}</span>
                  </div>
                  <p className="body-copy mt-2 text-xs opacity-45">
                    Complimentary shipping and returns on every order.
                  </p>
                  <button type="button" className="btn-solid mt-6">
                    <span>CHECKOUT →</span>
                  </button>
                </footer>
              </>
            )}
          </motion.aside>
        </div>
      )}
    </AnimatePresence>
  );
}
