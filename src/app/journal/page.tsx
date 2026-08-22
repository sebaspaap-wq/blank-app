import type { Metadata } from "next";
import Image from "next/image";
import { IMAGES } from "@/lib/images";
import RevealText from "@/components/ui/RevealText";

export const metadata: Metadata = {
  title: "Journal",
  description: "Notes on slow mornings, materials and the Mediterranean.",
};

const ENTRIES = [
  {
    title: "The seven-minute morning",
    category: "RITUAL",
    date: "JUNE",
    image: IMAGES.ivoryInterior,
    excerpt:
      "Before the messages, before the noise — a short account of the hours that belong to no one else.",
    ratio: "aspect-[4/5]",
    position: "object-[50%_32%]",
  },
  {
    title: "Where the cloth is made",
    category: "MATERIAL",
    date: "MAY",
    image: IMAGES.sandTerrace,
    excerpt:
      "Four generations, one loom room, and the particular sound of 550 gsm terry coming off the beam.",
    ratio: "aspect-[3/4]",
    position: "object-[52%_46%]",
  },
  {
    title: "A house above the water",
    category: "PLACES",
    date: "APRIL",
    image: IMAGES.cacaoSunset,
    excerpt:
      "Notes from a stone villa on the Ligurian coast, where the day is measured in shade rather than hours.",
    ratio: "aspect-[4/5]",
    position: "object-[58%_30%]",
  },
];

export default function JournalPage() {
  return (
    <div className="bg-ivory pb-32 md:pb-48">
      <header className="gutter pt-[calc(var(--nav-h)+5rem)] md:pt-[calc(var(--nav-h)+8rem)]">
        <p className="eyebrow opacity-45" data-reveal>
          JOURNAL
        </p>
        <RevealText
          as="h1"
          lines={["NOTES ON", "SLOW LIVING."]}
          className="font-serif-display mt-8 text-[clamp(2.5rem,9vw,7rem)]"
        />
      </header>

      <div className="mt-24 grid gap-x-10 gap-y-24 gutter md:mt-32 lg:grid-cols-3">
        {ENTRIES.map((entry, index) => (
          <article
            key={entry.title}
            className={`group/card ${index === 1 ? "lg:mt-24" : index === 2 ? "lg:mt-10" : ""}`}
            data-reveal
            style={{ ["--reveal-delay" as string]: `${index * 100}ms` }}
          >
            <div className={`media media-zoom relative ${entry.ratio} w-full`} data-cursor="view">
              <Image
                src={entry.image.src}
                alt={entry.image.alt}
                fill
                loading={index === 0 ? "eager" : "lazy"}
                sizes="(max-width: 768px) 92vw, 30vw"
                placeholder="blur"
                blurDataURL={entry.image.blurDataURL}
                className={`object-cover ${entry.position}`}
              />
            </div>

            <div className="mt-7 flex items-baseline justify-between">
              <span className="eyebrow opacity-40">{entry.category}</span>
              <span className="eyebrow opacity-25">{entry.date}</span>
            </div>
            <h2 className="font-serif-display mt-4 text-[1.6rem] leading-[1.15]">{entry.title}</h2>
            <p className="body-copy mt-4 text-[0.8125rem] opacity-50">{entry.excerpt}</p>
            <span className="link-line nav-label mt-6 opacity-60">
              <span>READ</span>
              <span aria-hidden className="arrow">→</span>
            </span>
          </article>
        ))}
      </div>
    </div>
  );
}
