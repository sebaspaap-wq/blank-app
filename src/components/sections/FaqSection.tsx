"use client";

import { useState } from "react";
import Link from "next/link";
import { Container, Eyebrow, Section } from "@/components/ui/Section";
import { faqs, type FaqItem } from "@/content/faq";
import { track } from "@/lib/analytics";
import { cx } from "@/lib/format";

function FaqRow({ item }: { item: FaqItem }) {
  const [open, setOpen] = useState(false);
  const panelId = `faq-panel-${item.id}`;
  const buttonId = `faq-button-${item.id}`;

  return (
    <div className="border-b border-charcoal/10">
      <h3>
        <button
          id={buttonId}
          type="button"
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => {
            const next = !open;
            setOpen(next);
            if (next) track("faq_opened", { label: item.id });
          }}
          className="flex w-full items-start justify-between gap-8 py-7 text-left transition-colors duration-300 hover:text-charcoal/70"
        >
          <span className="max-w-2xl text-[1.0625rem] font-medium tracking-[-0.015em] sm:text-[1.25rem]">
            {item.question}
          </span>
          <span
            aria-hidden="true"
            className={cx(
              "mt-1 shrink-0 text-2xl leading-none transition-transform duration-500 ease-[var(--ease-quit)]",
              open ? "rotate-45" : "rotate-0",
            )}
          >
            +
          </span>
        </button>
      </h3>
      <div
        id={panelId}
        role="region"
        aria-labelledby={buttonId}
        hidden={!open}
        className="pb-8"
      >
        {item.answer.map((paragraph) => (
          <p key={paragraph} className="max-w-2xl text-[0.9375rem] leading-relaxed text-charcoal/65 [&+p]:mt-4">
            {paragraph}
          </p>
        ))}
        {item.regulated ? (
          <p className="mt-5 max-w-2xl text-xs leading-relaxed text-charcoal/65">
            Medical wording on this answer follows the approved patient information. Always
            read the leaflet before use.
          </p>
        ) : null}
      </div>
    </div>
  );
}

export function FaqSection({
  limit,
  heading = "Questions, answered plainly.",
}: {
  limit?: number;
  heading?: string;
}) {
  const items = limit ? faqs.slice(0, limit) : faqs;

  return (
    <Section id="faq" tone="bone">
      <Container>
        <div className="grid gap-12 lg:grid-cols-[0.75fr_1.25fr] lg:gap-20">
          <div>
            <Eyebrow>FAQ</Eyebrow>
            <h2 className="mt-5 max-w-sm text-headline">{heading}</h2>
            {limit ? (
              <Link
                href="/faq"
                className="mt-8 inline-block text-[0.9375rem] font-medium underline-offset-4 hover:underline"
              >
                All questions →
              </Link>
            ) : null}
          </div>

          <div className="border-t border-charcoal/10">
            {items.map((item) => (
              <FaqRow key={item.id} item={item} />
            ))}
          </div>
        </div>
      </Container>
    </Section>
  );
}
