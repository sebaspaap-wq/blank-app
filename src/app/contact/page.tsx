import type { Metadata } from "next";
import Image from "next/image";
import { IMAGES } from "@/lib/images";
import RevealText from "@/components/ui/RevealText";

export const metadata: Metadata = {
  title: "Contact",
  description: "Client care, press and wholesale enquiries for CAVÁ.",
};

const CHANNELS = [
  {
    title: "CLIENT CARE",
    lines: ["care@cava.com", "Monday — Friday, 09:00 — 18:00 CET"],
  },
  { title: "PRESS", lines: ["press@cava.com"] },
  { title: "WHOLESALE", lines: ["trade@cava.com"] },
  { title: "ATELIER", lines: ["Rua do Almada 42", "4050-036 Porto, Portugal"] },
];

export default function ContactPage() {
  return (
    <div className="bg-ivory pb-32 md:pb-48">
      <header className="gutter pt-[calc(var(--nav-h)+5rem)] md:pt-[calc(var(--nav-h)+8rem)]">
        <p className="eyebrow opacity-45" data-reveal>
          CONTACT
        </p>
        <RevealText
          as="h1"
          lines={["WE ARE HERE,", "QUIETLY."]}
          className="font-serif-display mt-8 text-[clamp(2.5rem,9vw,7rem)]"
        />
      </header>

      <div className="mt-20 grid gap-16 gutter md:mt-28 md:grid-cols-2 md:gap-24">
        <div>
          <p className="body-copy max-w-[28rem] opacity-60" data-reveal>
            Every message is answered by a person, usually within one working day. For
            questions about an existing order, please include your order number.
          </p>

          <dl className="mt-16 grid gap-12 sm:grid-cols-2">
            {CHANNELS.map((channel, index) => (
              <div
                key={channel.title}
                data-reveal
                style={{ ["--reveal-delay" as string]: `${index * 90}ms` }}
                className="border-t border-[var(--hairline)] pt-6"
              >
                <dt className="eyebrow opacity-40">{channel.title}</dt>
                <dd className="mt-4">
                  {channel.lines.map((line) => (
                    <p key={line} className="body-copy text-[0.8125rem] opacity-65">
                      {line.includes("@") ? (
                        <a href={`mailto:${line}`} className="link-grow">
                          {line}
                        </a>
                      ) : (
                        line
                      )}
                    </p>
                  ))}
                </dd>
              </div>
            ))}
          </dl>
        </div>

        <div data-reveal="fade">
          <div className="img-reveal media relative aspect-[4/5] w-full" data-cursor="view">
          <Image
            src={IMAGES.cacaoPool.src}
            alt={IMAGES.cacaoPool.alt}
            fill
            sizes="(max-width: 768px) 92vw, 46vw"
            placeholder="blur"
            blurDataURL={IMAGES.cacaoPool.blurDataURL}
              className="object-cover object-[54%_30%]"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
