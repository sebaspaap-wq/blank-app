"use client";

import Link from "next/link";
import { useState } from "react";
import { useSite } from "@/components/site/SiteProvider";
import { PRODUCTS, SIZES, formatPrice, type Product, type Size } from "@/lib/products";
import Accordion from "./Accordion";

export default function ProductView({ product }: { product: Product }) {
  const { add } = useSite();
  const [size, setSize] = useState<Size | null>(null);
  const [nudge, setNudge] = useState(false);

  const handleAdd = () => {
    if (!size) {
      setNudge(true);
      window.setTimeout(() => setNudge(false), 2400);
      return;
    }
    add(product, size);
  };

  return (
    <div className="max-w-[30rem]">
      <p className="eyebrow opacity-45">CAVÁ</p>

      <h1 className="font-serif-display mt-6 text-[clamp(2rem,5vw,3.25rem)]">
        {product.name}
      </h1>

      <div className="mt-5 flex items-baseline gap-5">
        <span className="nav-label opacity-60">{product.colour}</span>
        <span className="price text-[0.9375rem]">{formatPrice(product.price)}</span>
      </div>

      <p className="body-copy mt-8 max-w-[26rem] opacity-60">{product.description}</p>

      {/* colour */}
      <div className="mt-12">
        <p className="eyebrow opacity-40">COLOUR — {product.colour}</p>
        <ul className="mt-5 flex items-center gap-4">
          {PRODUCTS.map((item) => (
            <li key={item.slug}>
              <Link
                href={`/collection/${item.slug}`}
                aria-label={item.colour}
                aria-current={item.slug === product.slug ? "page" : undefined}
                className="block p-[3px] transition-colors duration-500"
                style={{
                  border: `1px solid ${item.slug === product.slug ? "rgba(8,8,7,0.55)" : "transparent"}`,
                }}
              >
                <span
                  className="block h-7 w-7"
                  style={{
                    backgroundColor: item.swatch,
                    boxShadow: "inset 0 0 0 1px rgba(8,8,7,0.10)",
                  }}
                />
              </Link>
            </li>
          ))}
        </ul>
      </div>

      {/* size */}
      <div className="mt-10">
        <div className="flex items-baseline justify-between">
          <p className="eyebrow opacity-40">SIZE</p>
          <Link href="/service/size-guide" className="nav-label link-grow opacity-45">
            SIZE GUIDE
          </Link>
        </div>

        <ul className="mt-5 grid grid-cols-5 gap-2 xs:flex xs:flex-wrap xs:gap-2.5">
          {SIZES.map((value) => {
            const active = value === size;
            return (
              <li key={value}>
                <button
                  type="button"
                  onClick={() => setSize(value)}
                  aria-pressed={active}
                  className="nav-label w-full cursor-pointer border px-0 py-3.5 transition-all duration-500 xs:w-auto xs:px-6"
                  style={{
                    borderColor: active ? "var(--color-noir)" : "rgba(8,8,7,0.18)",
                    backgroundColor: active ? "var(--color-noir)" : "transparent",
                    color: active ? "var(--color-ivory)" : "inherit",
                    transitionTimingFunction: "var(--ease)",
                  }}
                >
                  {value}
                </button>
              </li>
            );
          })}
        </ul>

        <p
          className="eyebrow mt-4 h-3 opacity-70"
          aria-live="polite"
          style={{
            opacity: nudge ? 0.7 : 0,
            transition: "opacity 0.5s var(--ease)",
          }}
        >
          PLEASE SELECT A SIZE
        </p>
      </div>

      <button type="button" onClick={handleAdd} className="btn-solid mt-8">
        <span>ADD TO BAG</span>
      </button>

      <p className="body-copy mt-5 text-center text-[0.75rem] opacity-40">
        Complimentary shipping · 30-day returns
      </p>

      <div className="mt-14">
        <Accordion title="DETAILS" defaultOpen>
          <ul className="space-y-2.5">
            {product.details.map((detail) => (
              <li key={detail} className="body-copy text-[0.8125rem] opacity-60">
                {detail}
              </li>
            ))}
          </ul>
        </Accordion>

        <Accordion title="MATERIAL & CARE">
          <ul className="space-y-2.5">
            {product.material.map((line) => (
              <li key={line} className="body-copy text-[0.8125rem] opacity-60">
                {line}
              </li>
            ))}
          </ul>
        </Accordion>

        <Accordion title="SIZE GUIDE">
          <table className="w-full text-left">
            <thead>
              <tr className="eyebrow opacity-40">
                <th className="pb-3 font-normal">SIZE</th>
                <th className="pb-3 font-normal">CHEST</th>
                <th className="pb-3 font-normal">LENGTH</th>
              </tr>
            </thead>
            <tbody className="body-copy text-[0.8125rem] opacity-60">
              {[
                ["XS", "96 cm", "88 cm"],
                ["S", "102 cm", "90 cm"],
                ["M", "108 cm", "92 cm"],
                ["L", "116 cm", "94 cm"],
                ["XL", "124 cm", "96 cm"],
              ].map((row) => (
                <tr key={row[0]} className="border-t border-[var(--hairline)]">
                  {row.map((cell) => (
                    <td key={cell} className="py-2.5">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <p className="body-copy mt-4 text-[0.75rem] opacity-40">
            The signature robe is cut generously. For a closer fit, take one size down.
          </p>
        </Accordion>

        <Accordion title="SHIPPING & RETURNS">
          <p className="body-copy text-[0.8125rem] opacity-60">
            Complimentary shipping worldwide, dispatched within one working day from our
            atelier. Every order arrives wrapped in unbleached cotton. Returns are free
            within 30 days, unworn and in their original wrapping.
          </p>
        </Accordion>
      </div>
    </div>
  );
}
