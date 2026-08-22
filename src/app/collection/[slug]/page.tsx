import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { PRODUCTS, getProduct } from "@/lib/products";
import ProductView from "@/components/product/ProductView";
import ProductCard from "@/components/home/ProductCard";

type Params = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return PRODUCTS.map((product) => ({ slug: product.slug }));
}

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { slug } = await params;
  const product = getProduct(slug);
  if (!product) return {};

  return {
    title: `${product.name} — ${product.colour}`,
    description: product.description,
    openGraph: {
      title: `CAVÁ ${product.name} — ${product.colour}`,
      description: product.description,
      images: [{ url: product.hero.src }],
    },
  };
}

export default async function ProductPage({ params }: Params) {
  const { slug } = await params;
  const product = getProduct(slug);
  if (!product) notFound();

  const others = PRODUCTS.filter((item) => item.slug !== product.slug);

  return (
    <div className="bg-ivory pb-24 pt-[calc(var(--nav-h)+2rem)] md:pb-36">
      <nav aria-label="Breadcrumb" className="gutter">
        <ol className="eyebrow flex items-center gap-3 opacity-40">
          <li>
            <Link href="/collection" className="link-grow">
              COLLECTION
            </Link>
          </li>
          <li aria-hidden>—</li>
          <li aria-current="page">{product.colour}</li>
        </ol>
      </nav>

      <div className="mt-10 grid gap-12 gutter md:mt-14 md:grid-cols-[1.08fr_0.92fr] md:gap-12 lg:gap-20">
        {/* photography */}
        <div className="flex flex-col gap-4 md:gap-6">
          <div className="media relative aspect-[3/4] w-full" data-cursor="view">
            <Image
              src={product.hero.src}
              alt={product.hero.alt}
              fill
              priority
              sizes="(max-width: 768px) 92vw, 52vw"
              placeholder="blur"
              blurDataURL={product.hero.blurDataURL}
              className="object-cover"
            />
          </div>
          <div className="media relative aspect-[4/5] w-full" data-cursor="view">
            <div
              className="absolute inset-0"
              style={
                product.secondaryZoom
                  ? { transform: `scale(${product.secondaryZoom})` }
                  : undefined
              }
            >
              <Image
                src={product.secondary.src}
                alt={product.secondary.alt}
                fill
                loading="lazy"
                sizes="(max-width: 768px) 92vw, 52vw"
                placeholder="blur"
                blurDataURL={product.secondary.blurDataURL}
                className={`object-cover ${product.secondaryPosition}`}
              />
            </div>
          </div>
        </div>

        {/* information */}
        <div className="md:sticky md:top-[calc(var(--nav-h)+2rem)] md:h-fit md:pl-[6%]">
          <ProductView product={product} />
        </div>
      </div>

      <section className="mt-32 gutter md:mt-48">
        <div className="flex items-end justify-between gap-8">
          <h2 className="font-serif-display text-[clamp(1.5rem,4vw,2.5rem)]" data-reveal>
            Also in the collection
          </h2>
          <Link href="/collection" className="nav-label link-grow hidden opacity-45 md:block">
            ALL PIECES
          </Link>
        </div>

        <div className="mt-12 grid gap-x-8 gap-y-16 md:mt-16 md:grid-cols-2 lg:gap-x-14">
          {others.map((item, index) => (
            <ProductCard
              key={item.slug}
              product={item}
              delay={index * 90}
              sizes="(max-width: 768px) 92vw, 46vw"
            />
          ))}
        </div>
      </section>
    </div>
  );
}
