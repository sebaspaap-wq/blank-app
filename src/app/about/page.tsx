import type { Metadata } from "next";
import Image from "next/image";
import { IMAGES } from "@/lib/images";
import RevealText from "@/components/ui/RevealText";
import ArrowLink from "@/components/ui/ArrowLink";
import Parallax from "@/components/ui/Parallax";

export const metadata: Metadata = {
  title: "Our Story",
  description:
    "CAVÁ creates refined bathrobes designed to make everyday rituals feel extraordinary.",
};

const CHAPTERS = [
  {
    index: "01",
    title: "The mill",
    copy: "Our terry is woven on slow looms in northern Portugal by a family that has made cloth for four generations. 550 grams per square metre — heavy enough to hold warmth, fine enough to fall.",
  },
  {
    index: "02",
    title: "The wash",
    copy: "Every robe is garment washed before it leaves the atelier, so it arrives already soft. No coatings, no softeners, nothing that fades by the tenth wash.",
  },
  {
    index: "03",
    title: "The finish",
    copy: "Shawl collar, tonal piping, self-tie belt. The CAVÁ mark is embroidered in the same thread as the cloth — visible only to the person wearing it.",
  },
];

export default function AboutPage() {
  return (
    <div className="bg-ivory">
      <header className="gutter pt-[calc(var(--nav-h)+5rem)] md:pt-[calc(var(--nav-h)+8rem)]">
        <p className="eyebrow opacity-45" data-reveal>
          ABOUT CAVÁ
        </p>
        <RevealText
          as="h1"
          lines={["LUXURY,", "LIVED IN."]}
          className="font-serif-display mt-8 text-[clamp(2.75rem,10vw,8rem)]"
        />
      </header>

      <section className="mt-20 grid gap-14 gutter md:mt-28 md:grid-cols-2 md:gap-20">
        <div data-reveal="fade">
          <div className="img-reveal media relative aspect-[4/5] w-full" data-cursor="view">
            <Parallax amount={0.06} className="absolute inset-[-5%]">
            <Image
              src={IMAGES.sandTerrace.src}
              alt={IMAGES.sandTerrace.alt}
              fill
              priority
              sizes="(max-width: 768px) 92vw, 46vw"
              placeholder="blur"
              blurDataURL={IMAGES.sandTerrace.blurDataURL}
                className="object-cover object-[52%_28%]"
              />
            </Parallax>
          </div>
        </div>

        <div className="md:pt-16">
          <p className="body-copy max-w-[30rem] opacity-70" data-reveal>
            CAVÁ began with a simple observation: the objects we touch first in the
            morning set the tone for everything that follows. A robe is not a garment
            you perform in. It is the one you return to.
          </p>
          <p
            className="body-copy mt-7 max-w-[30rem] opacity-50"
            data-reveal
            style={{ ["--reveal-delay" as string]: "120ms" }}
          >
            So we made one piece, properly — the weight of hotel terry without the
            stiffness, the softness of home linen without the slouch. Three colours drawn
            from a Mediterranean morning: sand, ivory, cacao. Nothing else.
          </p>

          <blockquote
            className="font-serif-display mt-16 max-w-[26rem] text-[clamp(1.5rem,3.2vw,2.35rem)] leading-[1.25]"
            data-reveal
            style={{ ["--reveal-delay" as string]: "200ms" }}
          >
            “Luxury is not what you show. It is what you keep returning to.”
          </blockquote>
        </div>
      </section>

      <section className="mt-32 gutter md:mt-48">
        <div className="grid gap-14 md:grid-cols-3 md:gap-10">
          {CHAPTERS.map((chapter, index) => (
            <article
              key={chapter.index}
              data-reveal
              style={{ ["--reveal-delay" as string]: `${index * 110}ms` }}
              className="border-t border-[var(--hairline)] pt-8"
            >
              <p className="eyebrow opacity-30">{chapter.index}</p>
              <h2 className="font-serif-display mt-6 text-[1.75rem]">{chapter.title}</h2>
              <p className="body-copy mt-5 text-[0.8125rem] opacity-55">{chapter.copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="relative mt-32 h-[80svh] min-h-[30rem] overflow-hidden bg-noir md:mt-48">
        <Parallax amount={0.09} className="absolute inset-[-7%]">
          <Image
            src={IMAGES.cacaoSunset.src}
            alt={IMAGES.cacaoSunset.alt}
            fill
            loading="lazy"
            sizes="100vw"
            placeholder="blur"
            blurDataURL={IMAGES.cacaoSunset.blurDataURL}
            className="object-cover object-[58%_26%]"
          />
        </Parallax>
        <div
          aria-hidden
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(to bottom, rgba(8,8,7,0.35), rgba(8,8,7,0.05) 45%, rgba(8,8,7,0.6))",
          }}
        />
        <div className="relative flex h-full flex-col items-center justify-center gutter text-center text-ivory">
          <RevealText
            as="p"
            lines={["THE ART OF SLOW LIVING"]}
            className="font-serif-display text-[clamp(1.75rem,5vw,4rem)]"
          />
          <div className="mt-10" data-reveal style={{ ["--reveal-delay" as string]: "200ms" }}>
            <ArrowLink href="/collection">DISCOVER THE COLLECTION</ArrowLink>
          </div>
        </div>
      </section>
    </div>
  );
}
