import type { Metadata } from "next";
import Image from "next/image";
import { PRODUCTS } from "@/lib/products";
import ProductCard from "@/components/home/ProductCard";
import RevealText from "@/components/ui/RevealText";
import { IMAGES } from "@/lib/images";
import Parallax from "@/components/ui/Parallax";

export const metadata: Metadata = {
  title: "The Collection",
  description:
    "Three colours, one silhouette. The CAVÁ Signature Robe in Sand, Ivory and Cacao.",
};

export default function CollectionPage() {
  return (
    <div className="bg-ivory">
      <header className="gutter pt-[calc(var(--nav-h)+5rem)] md:pt-[calc(var(--nav-h)+8rem)]">
        <p className="eyebrow opacity-45" data-reveal>
          COLLECTION — SS
        </p>
        <RevealText
          as="h1"
          lines={["THE SIGNATURE", "ROBE."]}
          className="font-serif-display mt-8 text-[clamp(2.75rem,10vw,8rem)]"
        />
        <p
          className="body-copy mt-10 max-w-[32rem] opacity-55"
          data-reveal
          style={{ ["--reveal-delay" as string]: "160ms" }}
        >
          One cut, refined over three years. Woven from 550 gsm long-staple cotton terry,
          garment washed, and finished by hand in three enduring tones.
        </p>
      </header>

      <div className="mt-24 grid gap-x-8 gap-y-24 gutter md:mt-32 lg:grid-cols-3 lg:gap-x-12">
        {PRODUCTS.map((product, index) => (
          <div
            key={product.slug}
            className={index === 1 ? "lg:mt-24" : index === 2 ? "lg:mt-10" : undefined}
          >
            <ProductCard product={product} priority={index === 0} delay={index * 90} />
          </div>
        ))}
      </div>

      <section className="relative mt-32 h-[70svh] min-h-[26rem] overflow-hidden bg-noir md:mt-48">
        <Parallax amount={0.08} className="absolute inset-[-6%]">
          <Image
            src={IMAGES.cacaoPool.src}
            alt={IMAGES.cacaoPool.alt}
            fill
            loading="lazy"
            sizes="100vw"
            placeholder="blur"
            blurDataURL={IMAGES.cacaoPool.blurDataURL}
            className="object-cover object-[58%_28%]"
          />
        </Parallax>
        <div className="absolute inset-0 bg-noir/25" aria-hidden />
        <div className="relative flex h-full items-end gutter pb-14 text-ivory">
          <p className="font-serif-display max-w-[24rem] text-[clamp(1.5rem,3.5vw,2.5rem)]" data-reveal>
            Made in small quantities. Kept for years.
          </p>
        </div>
      </section>
    </div>
  );
}
