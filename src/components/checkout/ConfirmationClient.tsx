"use client";

import { useSyncExternalStore } from "react";
import { ButtonLink } from "@/components/ui/Button";
import { Container, Eyebrow } from "@/components/ui/Section";
import { formatPrice } from "@/lib/format";
import { timeline } from "@/content/timeline";

type LastOrder = {
  reference: string;
  totalCents: number;
  repeat: boolean;
  items: { name: string; quantity: number }[];
};

const ORDER_KEY = "quitter.lastOrder";

/** Read once, cached, so the snapshot stays referentially stable across renders. */
let cached: { raw: string | null; parsed: LastOrder | null } = { raw: null, parsed: null };

function readOrder(): LastOrder | null {
  let raw: string | null = null;
  try {
    raw = window.sessionStorage.getItem(ORDER_KEY);
  } catch {
    return null;
  }
  if (raw !== cached.raw) {
    try {
      cached = { raw, parsed: raw ? (JSON.parse(raw) as LastOrder) : null };
    } catch {
      cached = { raw, parsed: null };
    }
  }
  return cached.parsed;
}

const subscribeToOrder = () => () => {};

export function ConfirmationClient() {
  const order = useSyncExternalStore(subscribeToOrder, readOrder, () => null);

  return (
    <Container className="py-32 sm:py-40">
      <div className="max-w-2xl">
        <Eyebrow>Day 00</Eyebrow>
        <h1 className="mt-6 text-display">It starts now.</h1>
        <p className="mt-8 text-lede text-charcoal/65">
          Your programme is confirmed. You will get an email with your order details and
          your delivery date.
        </p>

        {order ? (
          <dl className="mt-12 space-y-4 border-t border-charcoal/10 pt-8 text-[0.9375rem]">
            <div className="flex justify-between gap-6">
              <dt className="text-charcoal/65">Reference</dt>
              <dd className="font-medium">{order.reference}</dd>
            </div>
            {order.items.map((item) => (
              <div key={item.name} className="flex justify-between gap-6">
                <dt className="text-charcoal/65">{item.name}</dt>
                <dd>× {item.quantity}</dd>
              </div>
            ))}
            <div className="flex justify-between gap-6 border-t border-charcoal/10 pt-4">
              <dt className="text-charcoal/65">Total</dt>
              <dd className="font-medium">{formatPrice(order.totalCents)}</dd>
            </div>
            <div className="flex justify-between gap-6">
              <dt className="text-charcoal/65">Repeat delivery</dt>
              <dd>{order.repeat ? "Once, in 90 days" : "None"}</dd>
            </div>
          </dl>
        ) : null}

        <div className="mt-14 border-t border-charcoal/10 pt-10">
          <h2 className="text-title">What happens next</h2>
          <ol className="mt-8 space-y-6">
            {timeline.map((milestone) => (
              <li key={milestone.day} className="flex gap-6">
                <span className="w-20 shrink-0 text-mono uppercase text-label">
                  {milestone.day}
                </span>
                <span className="text-[0.9375rem] text-charcoal/70">{milestone.title}</span>
              </li>
            ))}
          </ol>
        </div>

        <div className="mt-14 flex flex-wrap gap-3">
          <ButtonLink href="/how-it-works" size="lg" arrow>
            Read the 90-day plan
          </ButtonLink>
          <ButtonLink href="/patient-information" variant="outline" size="lg">
            Patient information
          </ButtonLink>
        </div>

        <p className="mt-10 text-xs leading-relaxed text-charcoal/65">
          No payment provider is connected in this build, so no money was taken and nothing
          will be dispatched.
        </p>
      </div>
    </Container>
  );
}
