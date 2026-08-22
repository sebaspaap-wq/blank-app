import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import RevealText from "@/components/ui/RevealText";

type Section = { heading: string; body: string };
type Entry = { title: string; lede: string; sections: Section[] };

const CONTENT: Record<string, Entry> = {
  shipping: {
    title: "Shipping",
    lede: "Complimentary worldwide shipping on every CAVÁ order.",
    sections: [
      {
        heading: "DISPATCH",
        body: "Orders placed before 14:00 CET are dispatched the same working day from our atelier in Porto. You will receive tracking by email as soon as the parcel leaves us.",
      },
      {
        heading: "DELIVERY",
        body: "Europe, two to four working days. United Kingdom, three to five. United States and Canada, four to six. Rest of world, five to nine.",
      },
      {
        heading: "PACKAGING",
        body: "Each robe is folded by hand, wrapped in unbleached cotton and sealed with a wax mark. Gift notes can be added at checkout at no cost.",
      },
      {
        heading: "DUTIES",
        body: "Orders shipped outside the European Union are delivered duties paid. There is nothing to settle on arrival.",
      },
    ],
  },
  returns: {
    title: "Returns",
    lede: "Thirty days, free of charge, in either direction.",
    sections: [
      {
        heading: "THE WINDOW",
        body: "Return anything unworn within thirty days of delivery. Robes should be returned unwashed, with their wrapping, so they can find another home.",
      },
      {
        heading: "HOW",
        body: "Write to care@cava.com with your order number and we will send a prepaid label the same day. Collection can be arranged from any address.",
      },
      {
        heading: "REFUNDS",
        body: "Refunds are issued to the original payment method within three working days of the parcel reaching us.",
      },
      {
        heading: "EXCHANGES",
        body: "Sizes and colours can be exchanged without limit. We hold your replacement while the first piece travels back.",
      },
    ],
  },
  "size-guide": {
    title: "Size Guide",
    lede: "One relaxed, unisex cut in five sizes.",
    sections: [
      {
        heading: "MEASUREMENTS",
        body: "XS — chest 96 cm, length 88 cm. S — 102 / 90. M — 108 / 92. L — 116 / 94. XL — 124 / 96. Measurements are taken flat and include the intended ease.",
      },
      {
        heading: "THE FIT",
        body: "The signature robe is cut generously and falls to mid-thigh. For a closer, shorter line, take one size down. Between sizes, most people prefer to size up.",
      },
      {
        heading: "AFTER WASHING",
        body: "Because every robe is garment washed before it leaves us, shrinkage is negligible — under one percent through the life of the piece.",
      },
    ],
  },
  care: {
    title: "Care",
    lede: "Terry improves with washing. Very little else is required.",
    sections: [
      {
        heading: "WASHING",
        body: "Machine wash at 40°C with like colours and a mild detergent. Skip the fabric softener — it coats the loops and takes the thirst out of the cloth.",
      },
      {
        heading: "DRYING",
        body: "Tumble dry on low. The heat lifts the pile back up. Line drying is fine, though the hand will be firmer.",
      },
      {
        heading: "LONGEVITY",
        body: "Do not bleach or dry clean. A pulled loop should be trimmed, never pulled through. Cared for this way, a CAVÁ robe is good for a decade of mornings.",
      },
    ],
  },
};

type Params = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return Object.keys(CONTENT).map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { slug } = await params;
  const entry = CONTENT[slug];
  if (!entry) return {};
  return { title: entry.title, description: entry.lede };
}

export default async function ServicePage({ params }: Params) {
  const { slug } = await params;
  const entry = CONTENT[slug];
  if (!entry) notFound();

  return (
    <div className="bg-ivory pb-32 md:pb-48">
      <header className="gutter pt-[calc(var(--nav-h)+5rem)] md:pt-[calc(var(--nav-h)+8rem)]">
        <p className="eyebrow opacity-45" data-reveal>
          CLIENT SERVICE
        </p>
        <RevealText
          as="h1"
          lines={[entry.title]}
          className="font-serif-display mt-8 text-[clamp(2.5rem,8vw,6rem)]"
        />
        <p
          className="body-copy mt-8 max-w-[30rem] opacity-55"
          data-reveal
          style={{ ["--reveal-delay" as string]: "140ms" }}
        >
          {entry.lede}
        </p>
      </header>

      <div className="mt-20 gutter md:mt-28">
        <div className="max-w-[46rem]">
          {entry.sections.map((section, index) => (
            <section
              key={section.heading}
              data-reveal
              style={{ ["--reveal-delay" as string]: `${index * 80}ms` }}
              className="grid gap-4 border-t border-[var(--hairline)] py-9 md:grid-cols-[10rem_1fr] md:gap-10"
            >
              <h2 className="eyebrow pt-1 opacity-40">{section.heading}</h2>
              <p className="body-copy opacity-65">{section.body}</p>
            </section>
          ))}
        </div>

        <div className="mt-16 border-t border-[var(--hairline)] pt-10">
          <p className="body-copy text-[0.8125rem] opacity-45">
            Still have a question?{" "}
            <Link href="/contact" className="link-grow opacity-100">
              Write to us
            </Link>
            .
          </p>
        </div>
      </div>
    </div>
  );
}
