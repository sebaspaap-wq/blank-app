import Image from "next/image";
import Link from "next/link";
import { IMAGES } from "@/lib/images";
import Parallax from "@/components/ui/Parallax";
import RevealText from "@/components/ui/RevealText";

const image = IMAGES.cacaoSunset;

export default function EditorialSection() {
  return (
    <section className="relative h-[92svh] min-h-[34rem] w-full overflow-hidden bg-noir text-ivory md:h-[100svh]">
      <Parallax amount={0.1} className="absolute inset-[-7%]">
        <Image
          src={image.src}
          alt={image.alt}
          fill
          sizes="100vw"
          placeholder="blur"
          blurDataURL={image.blurDataURL}
          className="object-cover object-[58%_34%] md:object-[56%_10%]"
        />
      </Parallax>

      <div
        aria-hidden
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(to bottom, rgba(8,8,7,0.42) 0%, rgba(8,8,7,0.12) 34%, rgba(8,8,7,0.28) 66%, rgba(8,8,7,0.62) 100%)",
        }}
      />

      <div className="relative flex h-full flex-col items-center justify-end gutter pb-[max(4rem,11vh)] text-center">
        <RevealText
          as="h2"
          lines={["SLOW DOWN."]}
          className="font-serif-display text-[clamp(3rem,12vw,10rem)]"
        />

        <p
          className="body-copy mt-8 max-w-[26rem] opacity-75"
          data-reveal
          style={{ ["--reveal-delay" as string]: "180ms" }}
        >
          A collection designed for life between the moments.
        </p>

        <div className="mt-10" data-reveal style={{ ["--reveal-delay" as string]: "280ms" }}>
          <Link href="/about" className="link-line nav-label">
            <span>EXPLORE THE CAVÁ WORLD</span>
            <span aria-hidden className="arrow">→</span>
          </Link>
        </div>
      </div>
    </section>
  );
}
