"use client";

import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import { IMAGES } from "@/lib/images";

type Item = {
  image: (typeof IMAGES)[keyof typeof IMAGES];
  caption: string;
  index: string;
  width: string;
  ratio: string;
  offset?: string;
  position?: string;
  zoom?: number;
};

const ITEMS: Item[] = [
  {
    image: IMAGES.sandTerrace,
    caption: "SAND — MORNING TERRACE",
    index: "01",
    width: "w-[68vw] xs:w-[20rem] md:w-[26rem]",
    ratio: "aspect-[3/4]",
    position: "object-[52%_28%]",
  },
  {
    image: IMAGES.sandTerrace,
    caption: "THE TERRY — 550 GSM",
    index: "02",
    width: "w-[52vw] xs:w-[15rem] md:w-[19rem]",
    ratio: "aspect-square",
    offset: "md:mt-28",
    position: "object-[46%_58%]",
    zoom: 2.1,
  },
  {
    image: IMAGES.ivoryInterior,
    caption: "IVORY — VILLA INTERIOR",
    index: "03",
    width: "w-[74vw] xs:w-[23rem] md:w-[32rem]",
    ratio: "aspect-[4/5]",
    offset: "md:mt-10",
    position: "object-[50%_32%]",
  },
  {
    image: IMAGES.cacaoSunset,
    caption: "CACAO — GOLDEN HOUR",
    index: "04",
    width: "w-[62vw] xs:w-[18rem] md:w-[23rem]",
    ratio: "aspect-[2/3]",
    position: "object-[58%_26%]",
  },
  {
    image: IMAGES.cacaoPool,
    caption: "THE POOL — 17:40",
    index: "05",
    width: "w-[80vw] xs:w-[26rem] md:w-[36rem]",
    ratio: "aspect-[5/4]",
    offset: "md:mt-24",
    position: "object-[54%_34%]",
  },
  {
    image: IMAGES.ivoryInterior,
    caption: "STILL — THE SHAWL COLLAR",
    index: "06",
    width: "w-[52vw] xs:w-[15rem] md:w-[19rem]",
    ratio: "aspect-square",
    offset: "md:mt-6",
    position: "object-[52%_30%]",
    zoom: 2.3,
  },
];

export default function Gallery() {
  const track = useRef<HTMLDivElement>(null);
  const [progress, setProgress] = useState(0);

  const update = useCallback(() => {
    const el = track.current;
    if (!el) return;
    const max = el.scrollWidth - el.clientWidth;
    setProgress(max <= 0 ? 0 : el.scrollLeft / max);
  }, []);

  useEffect(() => {
    const el = track.current;
    if (!el) return;
    update();
    el.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      el.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [update]);

  return (
    <section className="bg-ivory py-24 md:py-36" aria-label="Editorial gallery">
      <div className="gutter">
        <div className="flex items-end justify-between gap-8">
          <div>
            <p className="eyebrow opacity-45" data-reveal>
              CAMPAIGN — SS
            </p>
            <h2
              className="font-serif-display mt-6 text-[clamp(1.75rem,4.5vw,3.25rem)]"
              data-reveal
              style={{ ["--reveal-delay" as string]: "80ms" }}
            >
              An editorial in three tones
            </h2>
          </div>
          <p className="eyebrow hidden shrink-0 opacity-35 md:block" data-reveal>
            DRAG / SCROLL →
          </p>
        </div>
      </div>

      <div
        ref={track}
        className="no-scrollbar mt-14 flex gap-4 overflow-x-auto overscroll-x-contain pb-2 md:mt-20 md:gap-8"
        style={{ paddingLeft: "var(--gutter)", paddingRight: "var(--gutter)" }}
      >
        {ITEMS.map((item, index) => (
          <figure
            key={`${item.caption}-${index}`}
            className={`group/card shrink-0 ${item.width} ${item.offset ?? ""}`}
            data-reveal
            style={{ ["--reveal-delay" as string]: `${Math.min(index, 3) * 80}ms` }}
          >
            <div
              className={`media relative ${item.ratio} w-full`}
              data-cursor="view"
            >
              <div
                className="absolute inset-0"
                style={item.zoom ? { transform: `scale(${item.zoom})` } : undefined}
              >
                <Image
                  src={item.image.src}
                  alt={item.image.alt}
                  fill
                  loading="lazy"
                  sizes="(max-width: 768px) 80vw, 36rem"
                  placeholder="blur"
                  blurDataURL={item.image.blurDataURL}
                  className={`object-cover ${item.position ?? "object-center"} transition-transform duration-[1600ms] group-hover/card:scale-[1.04]`}
                />
              </div>
            </div>
            <figcaption className="mt-5 flex items-baseline justify-between gap-4">
              <span className="eyebrow opacity-45">{item.caption}</span>
              <span className="eyebrow opacity-25">{item.index}</span>
            </figcaption>
          </figure>
        ))}
      </div>

      <div className="gutter mt-12 md:mt-16">
        <div className="relative h-[1px] w-full bg-[rgba(8,8,7,0.12)]">
          <div
            className="absolute inset-y-0 left-0 bg-noir"
            style={{
              width: `${Math.max(8, progress * 100)}%`,
              transition: "width 0.25s var(--ease)",
            }}
          />
        </div>
      </div>
    </section>
  );
}
