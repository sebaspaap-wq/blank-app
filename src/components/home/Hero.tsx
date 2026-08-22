"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { IMAGES } from "@/lib/images";

const image = IMAGES.sandTerrace;

export default function Hero() {
  const [entered, setEntered] = useState(false);
  const frame = useRef<HTMLDivElement>(null);
  const veil = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const id = requestAnimationFrame(() => setEntered(true));
    return () => cancelAnimationFrame(id);
  }, []);

  // Departure: the hero settles back and dims as the collection arrives.
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    let raf = 0;
    const update = () => {
      raf = 0;
      const progress = Math.min(1, window.scrollY / window.innerHeight);
      if (frame.current) {
        frame.current.style.transform = `translate3d(0, ${progress * 8}%, 0) scale(${1 + progress * 0.06})`;
      }
      if (veil.current) {
        veil.current.style.opacity = `${progress * 0.55}`;
      }
    };

    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(update);
    };

    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  const t = (delay: number, duration = 1.4) =>
    `opacity ${duration}s var(--ease) ${delay}s, transform ${duration}s var(--ease) ${delay}s`;

  return (
    <section className="relative h-[100svh] w-full overflow-hidden bg-noir" aria-label="CAVÁ — The art of slow living">
      {/* photograph */}
      <div ref={frame} className="absolute inset-0 will-change-transform">
        <div
          className="absolute inset-0"
          style={{
            opacity: entered ? 1 : 0,
            transform: entered ? "scale(1)" : "scale(1.08)",
            transition: "opacity 2.4s var(--ease) 0.15s, transform 2.8s var(--ease) 0.15s",
          }}
        >
          <Image
            src={image.src}
            alt={image.alt}
            fill
            priority
            fetchPriority="high"
            sizes="100vw"
            placeholder="blur"
            blurDataURL={image.blurDataURL}
            className="object-cover object-[50%_50%] md:object-[52%_10%]"
          />
        </div>
      </div>

      {/* tonal grading — legibility without heaviness */}
      <div
        aria-hidden
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(to bottom, rgba(8,8,7,0.42) 0%, rgba(8,8,7,0.06) 26%, rgba(8,8,7,0.02) 45%, rgba(8,8,7,0.52) 88%, rgba(8,8,7,0.66) 100%)",
        }}
      />
      <div ref={veil} aria-hidden className="absolute inset-0 bg-noir" style={{ opacity: 0 }} />

      {/* opening curtain */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 z-30 bg-[#050504]"
        style={{
          opacity: entered ? 0 : 1,
          transition: "opacity 1.6s var(--ease) 0.1s",
        }}
      />

      {/* content */}
      <div className="absolute inset-0 z-20 flex flex-col justify-end gutter pb-[max(3.5rem,8vh)] text-ivory">
        <p
          className="eyebrow"
          style={{
            opacity: entered ? 0.82 : 0,
            transform: entered ? "translateY(0)" : "translateY(14px)",
            transition: t(1.05, 1.3),
          }}
        >
          THE ART OF SLOW LIVING
        </p>

        <h1 className="mt-6 overflow-hidden md:mt-8">
          <span
            className="wordmark block text-[clamp(3.75rem,15.5vw,13.5rem)]"
            style={{
              display: "block",
              transform: entered ? "translateY(0)" : "translateY(105%)",
              opacity: entered ? 1 : 0,
              transition: t(1.28, 1.7),
            }}
          >
            CAVÁ
          </span>
        </h1>

        <div
          className="mt-8 flex flex-col gap-6 md:mt-10 md:flex-row md:items-end md:justify-between"
          style={{
            opacity: entered ? 1 : 0,
            transform: entered ? "translateY(0)" : "translateY(18px)",
            transition: t(1.85, 1.4),
          }}
        >
          <Link href="/collection" className="link-line nav-label self-start">
            <span>DISCOVER THE COLLECTION</span>
            <span aria-hidden className="arrow">→</span>
          </Link>

          <div className="hidden items-center gap-4 md:flex">
            <span className="eyebrow opacity-55">SCROLL</span>
            <span className="relative block h-[1px] w-16 overflow-hidden bg-[rgba(245,242,235,0.28)]">
              <span className="absolute inset-0 origin-left bg-ivory" style={{ animation: "scroll-cue 3.4s var(--ease) infinite" }} />
            </span>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes scroll-cue {
          0% {
            transform: scaleX(0);
            transform-origin: left;
          }
          45% {
            transform: scaleX(1);
            transform-origin: left;
          }
          55% {
            transform: scaleX(1);
            transform-origin: right;
          }
          100% {
            transform: scaleX(0);
            transform-origin: right;
          }
        }
      `}</style>
    </section>
  );
}
