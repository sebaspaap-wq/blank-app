"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { PackShot } from "./PackShot";
import { Button } from "@/components/ui/Button";
import { Container, Eyebrow } from "@/components/ui/Section";
import { useCart } from "@/lib/cart";
import { euros, track } from "@/lib/analytics";
import { cx, formatPrice } from "@/lib/format";
import {
  individualValueCents,
  programs,
  savingCents,
  singleProducts,
  totalBoxes,
  defaultProgram,
  type Program,
} from "@/content/programs";
import { mandatoryNotice } from "@/content/medical";

/**
 * The buying module.
 *
 * One decision on screen at a time: which programme, then start. Individual
 * boxes stay available but never compete with the programme for attention.
 */
export function ProductPurchase() {
  const [selected, setSelected] = useState<Program>(defaultProgram);
  const { addItem } = useCart();
  const router = useRouter();
  const opened = useRef(false);

  useEffect(() => {
    if (opened.current) return;
    opened.current = true;
    track("program_selector_opened", { location: "product_page" });
  }, []);

  const saving = savingCents(selected);

  const select = (program: Program) => {
    setSelected(program);
    track("program_selected", {
      program_id: program.id,
      value: euros(program.priceCents),
      currency: "EUR",
      location: "product_page",
    });
  };

  const start = () => {
    addItem(
      {
        id: `program-${selected.id}`,
        kind: "program",
        name: `QUITTER 90 — ${selected.name}`,
        detail: `${totalBoxes(selected)} boxes · ${selected.durationDays} days`,
        priceCents: selected.priceCents,
      },
      1,
      "product_page",
    );
    router.push("/checkout");
  };

  const addBox = (id: string) => {
    const box = singleProducts.find((product) => product.id === id);
    if (!box) return;
    addItem(
      {
        id: box.id,
        kind: "box",
        name: box.name,
        detail: `${box.piecesPerBox} pieces`,
        priceCents: box.priceCents,
      },
      1,
      "product_page_single_box",
    );
    router.push("/checkout");
  };

  return (
    <section id="choose" className="scroll-mt-24 bg-bone pt-28 sm:pt-32 lg:pt-40">
      <Container>
        <div className="grid gap-14 lg:grid-cols-2 lg:gap-20">
          {/* Product stage */}
          <div className="relative lg:sticky lg:top-28 lg:self-start">
            <div className="relative mx-auto aspect-square w-full max-w-[21rem] sm:max-w-[32rem]">
              <div
                aria-hidden="true"
                className="absolute inset-[6%] rounded-full"
                style={{
                  background:
                    "radial-gradient(circle at 50% 42%, #ffffff 0%, rgba(247,246,242,0.5) 48%, rgba(247,246,242,0) 74%)",
                }}
              />
              <div className="pack-enter absolute left-[4%] top-[10%] w-[56%]">
                <PackShot strength="4 mg" angle={-19} priority />
              </div>
              <div className="pack-enter absolute right-[2%] top-[30%] w-[48%]">
                <PackShot strength="2 mg" angle={-12} />
              </div>
            </div>
            <p className="mt-4 text-center text-mono uppercase text-label">
              QUITTER 2 mg &amp; 4 mg · medicated chewing gum
            </p>
          </div>

          {/* Buying panel */}
          <div>
            <Eyebrow>90-day programme</Eyebrow>
            <h1 className="mt-5 text-headline">QUITTER 90</h1>
            <p className="mt-6 max-w-md text-lede text-charcoal/65">
              Everything the next ninety days need, in one delivery. Choose the programme
              that matches how much you smoke today.
            </p>

            <div className="mt-10 space-y-3" role="radiogroup" aria-label="Choose your programme">
              {programs.map((program) => {
                const active = program.id === selected.id;
                return (
                  <button
                    key={program.id}
                    type="button"
                    role="radio"
                    aria-checked={active}
                    onClick={() => select(program)}
                    className={cx(
                      "flex w-full items-center justify-between gap-6 rounded-2xl border p-5 text-left transition-all duration-300 ease-[var(--ease-quit)] sm:p-6",
                      active
                        ? "border-charcoal bg-white shadow-[var(--shadow-card)]"
                        : "border-charcoal/12 hover:border-charcoal/35",
                    )}
                  >
                    <span>
                      <span className="flex items-center gap-3">
                        <span className="text-[1.0625rem] font-semibold tracking-[-0.02em]">
                          {program.name}
                        </span>
                        {program.popular ? (
                          <span className="rounded-full bg-charcoal/[0.06] px-2.5 py-1 text-mono uppercase text-charcoal/65">
                            Most popular
                          </span>
                        ) : null}
                      </span>
                      <span className="mt-1.5 block text-[0.875rem] text-charcoal/65">
                        {program.audience} · {totalBoxes(program)} boxes
                      </span>
                    </span>
                    <span className="shrink-0 text-right">
                      <span className="block text-[1.0625rem] font-semibold">
                        {formatPrice(program.priceCents)}
                      </span>
                      {savingCents(program) > 0 ? (
                        <span className="mt-1 block text-[0.8125rem] text-label">
                          save {formatPrice(savingCents(program))}
                        </span>
                      ) : null}
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="mt-8 border-t border-charcoal/10 pt-8">
              <div className="flex items-end justify-between gap-6">
                <div>
                  <p className="text-[2.25rem] font-semibold leading-none tracking-[-0.04em]">
                    {formatPrice(selected.priceCents)}
                  </p>
                  {saving > 0 ? (
                    <p className="mt-3 text-[0.9375rem] text-charcoal/65">
                      <span className="line-through decoration-charcoal/30">
                        {formatPrice(individualValueCents(selected))}
                      </span>{" "}
                      bought box by box — you keep {formatPrice(saving)}
                    </p>
                  ) : null}
                </div>
                <p className="text-right text-[0.8125rem] text-charcoal/65">
                  {selected.durationDays} days
                  <br />
                  {totalBoxes(selected)} boxes
                </p>
              </div>

              <Button size="lg" className="mt-7 w-full" onClick={start} arrow>
                Start my 90 days
              </Button>
              <p className="mt-4 text-center text-[0.8125rem] text-charcoal/65">
                One-off purchase · free delivery · nothing renews automatically
              </p>
            </div>

            <ul className="mt-10 space-y-3 border-t border-charcoal/10 pt-8">
              {selected.includes.map((item) => (
                <li key={item} className="flex gap-4 text-[0.9375rem] text-charcoal/70">
                  <span aria-hidden="true" className="mt-2 block size-1 shrink-0 rounded-full bg-taupe" />
                  {item}
                </li>
              ))}
            </ul>

            <details className="mt-8 border-t border-charcoal/10 pt-6">
              <summary className="cursor-pointer text-[0.9375rem] text-charcoal/65 transition-colors hover:text-charcoal">
                Prefer a single box?
              </summary>
              <div className="mt-5 space-y-3">
                {singleProducts.map((box) => (
                  <div
                    key={box.id}
                    className="flex items-center justify-between gap-6 rounded-2xl border border-charcoal/12 p-5"
                  >
                    <span>
                      <span className="block text-[0.9375rem] font-medium">{box.name}</span>
                      <span className="mt-1 block text-[0.8125rem] text-charcoal/65">
                        {box.piecesPerBox} pieces · {formatPrice(box.priceCents)}
                      </span>
                    </span>
                    <Button variant="outline" onClick={() => addBox(box.id)}>
                      Add box
                    </Button>
                  </div>
                ))}
              </div>
            </details>

            <p className="mt-8 text-xs leading-relaxed text-charcoal/65">{mandatoryNotice}</p>
          </div>
        </div>
      </Container>
    </section>
  );
}
