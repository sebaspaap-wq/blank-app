"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useSite } from "./SiteProvider";

export default function Navigation() {
  const pathname = usePathname();
  const { count, overlay, toggle, open } = useSite();
  const overHero = pathname === "/";

  const [solid, setSolid] = useState(!overHero);
  const [hidden, setHidden] = useState(false);
  const [entered, setEntered] = useState(false);
  const lastY = useRef(0);

  useEffect(() => {
    setSolid(!overHero);
  }, [overHero]);

  useEffect(() => {
    const id = window.setTimeout(() => setEntered(true), overHero ? 900 : 60);
    return () => window.clearTimeout(id);
  }, [overHero]);

  useEffect(() => {
    let frame = 0;

    const evaluate = () => {
      frame = 0;
      const y = window.scrollY;
      const threshold = overHero ? window.innerHeight * 0.82 : 0;

      // Over the hero the bar is transparent with white type; everywhere else
      // it always carries its own ground so it can never disappear.
      setSolid(overHero ? y > threshold : true);
      setHidden(y > threshold + 200 && y > lastY.current + 4);
      lastY.current = y;
    };

    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(evaluate);
    };

    evaluate();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [overHero]);

  // While an overlay is open the bar stays put and inherits overlay colours.
  const menuOpen = overlay === "menu";
  const searchOpen = overlay === "search";
  const onImage = overHero && !solid && !menuOpen && !searchOpen;

  return (
    <header
      className="fixed inset-x-0 top-0 z-[90] will-change-transform"
      style={{
        transform: hidden && !overlay ? "translate3d(0,-100%,0)" : "translate3d(0,0,0)",
        transition: "transform 0.85s var(--ease)",
      }}
    >
      <div
        className="absolute inset-0 border-b"
        style={{
          backgroundColor: "rgba(245,242,235,0.92)",
          backdropFilter: "saturate(140%) blur(14px)",
          WebkitBackdropFilter: "saturate(140%) blur(14px)",
          borderColor: "rgba(8,8,7,0.09)",
          opacity: solid && !menuOpen ? 1 : 0,
          transition: "opacity 0.9s var(--ease)",
        }}
        aria-hidden
      />

      <nav
        aria-label="Primary"
        className="relative flex items-center justify-between gutter"
        style={{
          height: solid && !menuOpen ? "4.5rem" : "var(--nav-h)",
          color: onImage || menuOpen ? "#F5F2EB" : "#080807",
          opacity: entered ? 1 : 0,
          transition:
            "height 0.9s var(--ease), color 0.7s var(--ease), opacity 1.4s var(--ease)",
        }}
      >
        {/* left — MENU (desktop) */}
        <div className="hidden flex-1 md:block">
          <button
            type="button"
            onClick={() => toggle("menu")}
            className="nav-label link-grow cursor-pointer"
            aria-expanded={menuOpen}
            aria-controls="cava-menu"
          >
            {menuOpen ? "CLOSE" : "MENU"}
          </button>
        </div>

        {/* left — wordmark (mobile) */}
        <Link
          href="/"
          className="wordmark text-[1.05rem] md:hidden"
          aria-label="CAVÁ — home"
        >
          CAVÁ
        </Link>

        {/* centre — wordmark (desktop) */}
        <Link
          href="/"
          aria-label="CAVÁ — home"
          className="wordmark absolute left-1/2 hidden -translate-x-1/2 md:block"
          style={{
            fontSize: solid && !menuOpen ? "1.15rem" : "1.4rem",
            transition: "font-size 0.9s var(--ease)",
          }}
        >
          CAVÁ
        </Link>

        {/* right */}
        <div className="flex flex-1 items-center justify-end gap-6 md:gap-8">
          <button
            type="button"
            onClick={() => toggle("search")}
            className="nav-label link-grow hidden cursor-pointer md:inline-block"
          >
            SEARCH
          </button>
          <button
            type="button"
            onClick={() => toggle("menu")}
            className="nav-label link-grow cursor-pointer md:hidden"
            aria-expanded={menuOpen}
            aria-controls="cava-menu"
          >
            {menuOpen ? "CLOSE" : "MENU"}
          </button>
          <button
            type="button"
            onClick={() => open("bag")}
            className="nav-label link-grow cursor-pointer"
            aria-label={`Bag, ${count} item${count === 1 ? "" : "s"}`}
          >
            BAG <span className="tabular-nums">({count})</span>
          </button>
        </div>
      </nav>
    </header>
  );
}
