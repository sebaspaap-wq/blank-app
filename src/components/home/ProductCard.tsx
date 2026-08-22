import Image from "next/image";
import Link from "next/link";
import { formatPrice, type Product } from "@/lib/products";

type Props = {
  product: Product;
  priority?: boolean;
  delay?: number;
  sizes?: string;
};

export default function ProductCard({
  product,
  priority = false,
  delay = 0,
  sizes = "(max-width: 768px) 92vw, (max-width: 1280px) 33vw, 30vw",
}: Props) {
  return (
    <article data-reveal style={{ ["--reveal-delay" as string]: `${delay}ms` }}>
      <Link href={`/collection/${product.slug}`} className="group/card block">
        <div className="media media-zoom relative aspect-[3/4] w-full" data-cursor="view">
          <Image
            src={product.card.src}
            alt={product.card.alt}
            fill
            sizes={sizes}
            priority={priority}
            loading={priority ? "eager" : "lazy"}
            placeholder="blur"
            blurDataURL={product.card.blurDataURL}
            className={`object-cover ${product.cardPosition}`}
          />
        </div>

        <div
          className="transition-transform duration-[900ms] group-hover/card:-translate-y-1.5"
          style={{ transitionTimingFunction: "var(--ease)" }}
        >
          <div className="mt-7 flex items-baseline justify-between gap-6">
            <h3 className="nav-label">{product.colour}</h3>
            <span className="price">{formatPrice(product.price)}</span>
          </div>

          <p className="font-serif-display mt-3 text-[1.35rem] md:text-[1.5rem]">{product.name}</p>
          <p className="body-copy mt-1.5 text-[0.8125rem] opacity-50">{product.subtitle}</p>

          <span className="link-line nav-label mt-6 opacity-70 transition-opacity duration-700 group-hover/card:opacity-100">
            <span>DISCOVER</span>
            <span aria-hidden className="arrow">→</span>
          </span>
        </div>
      </Link>
    </article>
  );
}
