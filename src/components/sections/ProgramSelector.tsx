"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ProgramCard } from "@/components/product/ProgramCard";
import { Button } from "@/components/ui/Button";
import { Container, Eyebrow, Section } from "@/components/ui/Section";
import { useCart } from "@/lib/cart";
import { euros, track } from "@/lib/analytics";
import { formatPrice } from "@/lib/format";
import {
  defaultProgram,
  programs,
  savingCents,
  totalBoxes,
  type Program,
} from "@/content/programs";
import { mandatoryNotice } from "@/content/medical";

/**
 * The commercial centre of the site: three programmes, one obvious next step.
 * Selection is local state; nothing is added to the cart until the visitor
 * asks for it.
 */
export function ProgramSelector({ heading = "Choose your journey." }: { heading?: string }) {
  const [selected, setSelected] = useState<Program>(defaultProgram);
  const { addItem } = useCart();
  const router = useRouter();
  const sectionRef = useRef<HTMLDivElement | null>(null);
  const opened = useRef(false);

  useEffect(() => {
    const node = sectionRef.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting && !opened.current) {
            opened.current = true;
            track("program_selector_opened", { location: "program_selector" });
            observer.disconnect();
          }
        }
      },
      { threshold: 0.25 },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  const handleSelect = (program: Program) => {
    setSelected(program);
    track("program_selected", {
      program_id: program.id,
      value: euros(program.priceCents),
      currency: "EUR",
    });
  };

  const handleStart = () => {
    addItem(
      {
        id: `program-${selected.id}`,
        kind: "program",
        name: `QUITTER 90 — ${selected.name}`,
        detail: `${totalBoxes(selected)} boxes · ${selected.durationDays} days`,
        priceCents: selected.priceCents,
      },
      1,
      "program_selector",
    );
    router.push("/checkout");
  };

  const saving = savingCents(selected);

  return (
    <Section id="choose" tone="deep">
      <Container>
        <div ref={sectionRef}>
          <div className="max-w-2xl">
            <Eyebrow>The programme</Eyebrow>
            <h2 className="mt-5 text-headline">{heading}</h2>
            <p className="mt-6 max-w-xl text-lede text-charcoal/65">
              Three 90-day plans. Same programme, different amount of gum. Pick the one
              that matches how much you smoke today — you can always ask your pharmacist.
            </p>
          </div>

          <div className="mt-14 grid gap-5 md:grid-cols-3">
            {programs.map((program) => (
              <ProgramCard
                key={program.id}
                program={program}
                selected={selected.id === program.id}
                onSelect={handleSelect}
              />
            ))}
          </div>

          <div className="mt-10 flex flex-col gap-6 rounded-[20px] bg-white p-7 shadow-[var(--shadow-card)] sm:flex-row sm:items-center sm:justify-between sm:p-9">
            <div>
              <p className="text-mono uppercase text-label">Your selection</p>
              <p className="mt-3 text-title">
                QUITTER 90 — {selected.name}
              </p>
              <p className="mt-2 text-sm text-charcoal/65">
                {formatPrice(selected.priceCents)} · {totalBoxes(selected)} boxes ·{" "}
                {selected.durationDays} days
                {saving > 0 ? ` · you keep ${formatPrice(saving)}` : ""}
              </p>
            </div>
            <Button size="lg" onClick={handleStart} arrow className="shrink-0">
              Start my 90 days
            </Button>
          </div>

          <p className="mt-8 max-w-3xl text-xs leading-relaxed text-charcoal/65">
            {mandatoryNotice} Programme names describe how much gum is included, not a
            medical assessment. Dosing guidance follows the approved patient information.
          </p>
        </div>
      </Container>
    </Section>
  );
}
