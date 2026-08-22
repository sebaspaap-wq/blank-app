import Image from "next/image";
import { IMAGES } from "@/lib/images";
import RevealText from "@/components/ui/RevealText";
import ArrowLink from "@/components/ui/ArrowLink";
import Parallax from "@/components/ui/Parallax";

const image = IMAGES.ivoryInterior;

export default function About() {
  return (
    <section id="about" className="bg-ivory pb-28 pt-8 md:pb-44 md:pt-16">
      <div className="grid items-center gap-16 gutter md:grid-cols-2 md:gap-20 lg:gap-28">
        <div className="order-2 md:order-1 md:pr-[8%] lg:pl-[6%]">
          <p className="eyebrow opacity-45" data-reveal>
            ABOUT CAVÁ
          </p>

          <RevealText
            as="h2"
            lines={["LUXURY,", "LIVED IN."]}
            className="font-serif-display mt-8 text-[clamp(2.75rem,8vw,5.5rem)]"
          />

          <p
            className="body-copy mt-10 max-w-[30rem] opacity-65"
            data-reveal
            style={{ ["--reveal-delay" as string]: "140ms" }}
          >
            CAVÁ creates refined bathrobes designed to make everyday rituals feel
            extraordinary.
          </p>

          <p
            className="body-copy mt-6 max-w-[30rem] opacity-45"
            data-reveal
            style={{ ["--reveal-delay" as string]: "220ms" }}
          >
            Each piece is woven in a small family mill, washed until it falls softly,
            and finished by hand — made to be worn a thousand mornings rather than one
            season.
          </p>

          <div className="mt-12" data-reveal style={{ ["--reveal-delay" as string]: "300ms" }}>
            <ArrowLink href="/about">OUR STORY</ArrowLink>
          </div>
        </div>

        <div className="order-1 md:order-2">
          <div data-reveal="fade">
            <div className="img-reveal media relative aspect-[4/5] w-full md:aspect-[3/4]" data-cursor="view">
              <Parallax amount={0.07} className="absolute inset-[-6%]">
              <Image
                src={image.src}
                alt={image.alt}
                fill
                sizes="(max-width: 768px) 92vw, 46vw"
                placeholder="blur"
                blurDataURL={image.blurDataURL}
                  className="object-cover object-[50%_35%]"
                />
              </Parallax>
            </div>
          </div>
          <p className="eyebrow mt-6 opacity-35" data-reveal>
            THE SIGNATURE ROBE — IVORY · PORTOFINO, 07:14
          </p>
        </div>
      </div>
    </section>
  );
}
