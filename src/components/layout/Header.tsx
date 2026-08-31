"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "./Logo";
import { ButtonLink } from "@/components/ui/Button";
import { Container } from "@/components/ui/Section";
import { cta, primaryNav } from "@/content/site";
import { useCart } from "@/lib/cart";
import { cx } from "@/lib/format";

export function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();
  const { count } = useCart();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  return (
    <header
      className={cx(
        "fixed inset-x-0 top-0 z-50 transition-[background-color,backdrop-filter,border-color] duration-500 ease-[var(--ease-quit)]",
        scrolled || menuOpen
          ? "border-b border-charcoal/8 bg-bone/85 backdrop-blur-xl"
          : "border-b border-transparent",
      )}
    >
      <Container>
        <div className="flex h-16 items-center justify-between gap-6 sm:h-20">
          <Logo />

          <nav aria-label="Primary" className="hidden lg:block">
            <ul className="flex items-center gap-9">
              {primaryNav.map((item) => {
                const active = pathname === item.href;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      aria-current={active ? "page" : undefined}
                      className={cx(
                        "text-[0.9375rem] transition-colors duration-300",
                        active ? "text-charcoal" : "text-charcoal/65 hover:text-charcoal",
                      )}
                    >
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          <div className="flex items-center gap-3">
            <Link
              href="/checkout"
              className="hidden text-[0.9375rem] text-charcoal/65 transition-colors hover:text-charcoal sm:inline"
            >
              Bag{count > 0 ? ` (${count})` : ""}
            </Link>
            <span className="hidden sm:block">
              <ButtonLink href={cta.primary.href}>{cta.primary.label}</ButtonLink>
            </span>

            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              aria-expanded={menuOpen}
              aria-controls="mobile-menu"
              className="-mr-2 flex size-11 items-center justify-center lg:hidden"
            >
              <span className="sr-only">{menuOpen ? "Close menu" : "Open menu"}</span>
              <span aria-hidden="true" className="relative block h-3 w-6">
                <span
                  className={cx(
                    "absolute left-0 block h-px w-6 bg-charcoal transition-transform duration-300 ease-[var(--ease-quit)]",
                    menuOpen ? "top-1.5 rotate-45" : "top-0",
                  )}
                />
                <span
                  className={cx(
                    "absolute left-0 block h-px w-6 bg-charcoal transition-transform duration-300 ease-[var(--ease-quit)]",
                    menuOpen ? "top-1.5 -rotate-45" : "top-3",
                  )}
                />
              </span>
            </button>
          </div>
        </div>
      </Container>

      <div
        id="mobile-menu"
        hidden={!menuOpen}
        className="border-t border-charcoal/8 bg-bone lg:hidden"
      >
        <Container>
          <nav aria-label="Mobile" className="py-6">
            <ul className="space-y-1">
              {primaryNav.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={() => setMenuOpen(false)}
                    className="flex items-baseline justify-between gap-6 border-b border-charcoal/8 py-4"
                  >
                    <span className="text-[1.375rem] tracking-[-0.02em]">{item.label}</span>
                    {item.description ? (
                      <span className="text-mono uppercase text-label">{item.description}</span>
                    ) : null}
                  </Link>
                </li>
              ))}
              <li>
                <Link
                  href="/checkout"
                  onClick={() => setMenuOpen(false)}
                  className="flex items-baseline justify-between gap-6 border-b border-charcoal/8 py-4"
                >
                  <span className="text-[1.375rem] tracking-[-0.02em]">Bag</span>
                  <span className="text-mono uppercase text-label">{count} items</span>
                </Link>
              </li>
            </ul>
            <ButtonLink
              href={cta.primary.href}
              size="lg"
              className="mt-7 w-full"
              onClick={() => setMenuOpen(false)}
              arrow
            >
              {cta.primary.label}
            </ButtonLink>
          </nav>
        </Container>
      </div>
    </header>
  );
}
