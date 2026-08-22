import { PRODUCTS } from "@/lib/products";
import ProductCard from "./ProductCard";
import RevealText from "@/components/ui/RevealText";
import ArrowLink from "@/components/ui/ArrowLink";

export default function Collection() {
  return (
    <section id="collection" className="bg-ivory pb-24 pt-24 md:pb-40 md:pt-36">
      <div className="gutter">
        <header className="mx-auto max-w-[46rem] text-center">
          <p className="eyebrow opacity-45" data-reveal>
            THREE COLOURS · ONE RITUAL
          </p>
          <RevealText
            as="h2"
            lines={["THE COLLECTION"]}
            className="font-serif-display mt-7 text-[clamp(2.25rem,7vw,5rem)]"
          />
          <p
            className="body-copy mx-auto mt-8 max-w-[34rem] opacity-55"
            data-reveal
            style={{ ["--reveal-delay" as string]: "160ms" }}
          >
            Woven in Portugal from long-staple cotton, cut in a single silhouette and
            offered in the three tones of a Mediterranean morning.
          </p>
        </header>

        {/* asymmetric editorial rhythm — never a grid of cards */}
        <div className="mt-20 grid gap-x-8 gap-y-20 md:mt-28 lg:grid-cols-3 lg:gap-x-10">
          {PRODUCTS.map((product, index) => (
            <div
              key={product.slug}
              className={
                index === 1 ? "lg:mt-32" : index === 2 ? "lg:mt-14" : undefined
              }
            >
              <ProductCard product={product} delay={index * 90} />
            </div>
          ))}
        </div>

        <div className="mt-24 flex justify-center md:mt-36" data-reveal>
          <ArrowLink href="/collection">VIEW THE FULL COLLECTION</ArrowLink>
        </div>
      </div>
    </section>
  );
}
