"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Container, Eyebrow } from "@/components/ui/Section";
import { useCart } from "@/lib/cart";
import { euros, track } from "@/lib/analytics";
import { cx, formatPrice } from "@/lib/format";
import { defaultProgram, totalBoxes } from "@/content/programs";
import { mandatoryNotice } from "@/content/medical";

const PAYMENT_METHODS = [
  { id: "ideal", label: "iDEAL", detail: "Pay from your own bank" },
  { id: "card", label: "Card", detail: "Visa, Mastercard" },
  { id: "bancontact", label: "Bancontact", detail: "For Belgian accounts" },
] as const;

const COUNTRIES = [
  { code: "NL", label: "Netherlands" },
  { code: "BE", label: "Belgium" },
] as const;

type Field = {
  id: string;
  label: string;
  autoComplete: string;
  type?: string;
  width?: "full" | "half";
  inputMode?: "text" | "email" | "numeric" | "tel";
};

const deliveryFields: Field[] = [
  { id: "email", label: "Email", autoComplete: "email", type: "email", inputMode: "email" },
  { id: "name", label: "Full name", autoComplete: "name" },
  { id: "street", label: "Street and number", autoComplete: "street-address" },
  { id: "postcode", label: "Postcode", autoComplete: "postal-code", width: "half" },
  { id: "city", label: "City", autoComplete: "address-level2", width: "half" },
];

/**
 * Checkout.
 *
 * One page, four blocks: what you are buying, where it goes, how you pay, what
 * it costs. Nothing is pre-ticked, no countdowns, no scarcity messaging, and
 * the repeat-delivery option states its charge in full before it can be chosen.
 *
 * PAYMENT: this build has no payment provider connected. `submitOrder` is the
 * single integration point — swap it for a call that creates the payment and
 * redirects to the provider.
 */
export function CheckoutClient() {
  const { items, subtotalCents, clear, setQuantity, ready } = useCart();
  const router = useRouter();
  const [payment, setPayment] = useState<(typeof PAYMENT_METHODS)[number]["id"]>("ideal");
  const [country, setCountry] = useState<string>("NL");
  const [repeat, setRepeat] = useState(false);
  const [confirmedAge, setConfirmedAge] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const empty = ready && items.length === 0;

  useEffect(() => {
    if (!ready || items.length === 0) return;
    track("checkout_started", {
      value: euros(subtotalCents),
      currency: "EUR",
      quantity: items.reduce((sum, item) => sum + item.quantity, 0),
    });
    // Fires once per checkout entry with a non-empty bag.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready]);

  const shippingCents = 0;
  const totalCents = useMemo(() => subtotalCents + shippingCents, [subtotalCents]);

  const submitOrder = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!confirmedAge) {
      setError("Please confirm you are 18 or over before ordering a medicine.");
      return;
    }
    setError(null);
    setSubmitting(true);

    const reference = `Q-${Date.now().toString(36).toUpperCase()}`;

    track("purchase_completed", {
      value: euros(totalCents),
      currency: "EUR",
      order_reference: reference,
      quantity: items.reduce((sum, item) => sum + item.quantity, 0),
    });
    if (repeat) {
      track("subscription_started", { value: euros(totalCents), currency: "EUR" });
    }

    try {
      window.sessionStorage.setItem(
        "quitter.lastOrder",
        JSON.stringify({
          reference,
          totalCents,
          repeat,
          items: items.map((item) => ({ name: item.name, quantity: item.quantity })),
        }),
      );
    } catch {
      /* Confirmation page falls back to a generic message. */
    }

    clear();
    router.push("/checkout/confirmation");
  };

  if (empty) {
    return (
      <Container className="flex min-h-[70vh] flex-col justify-center py-32">
        <Eyebrow>Your bag</Eyebrow>
        <h1 className="mt-6 max-w-xl text-headline">Nothing in the bag yet.</h1>
        <p className="mt-6 max-w-md text-lede text-charcoal/65">
          The {defaultProgram.name} programme is where most people start:{" "}
          {totalBoxes(defaultProgram)} boxes across {defaultProgram.durationDays} days for{" "}
          {formatPrice(defaultProgram.priceCents)}.
        </p>
        <div className="mt-10">
          <ButtonLink href="/programs" size="lg" arrow>
            Choose your programme
          </ButtonLink>
        </div>
      </Container>
    );
  }

  return (
    <Container className="py-28 sm:py-32">
      <div className="grid gap-14 lg:grid-cols-[1.15fr_0.85fr] lg:gap-20">
        <form onSubmit={submitOrder} noValidate={false} className="order-2 lg:order-1">
          {/* 1 — Product */}
          <section aria-labelledby="product-heading">
            <Eyebrow>Step 1</Eyebrow>
            <h2 id="product-heading" className="mt-4 text-title">
              Your programme
            </h2>
            <ul className="mt-7 divide-y divide-charcoal/10 border-y border-charcoal/10">
              {items.map((item) => (
                <li key={item.id} className="flex items-center justify-between gap-6 py-5">
                  <div>
                    <p className="text-[1.0625rem] font-medium tracking-[-0.015em]">
                      {item.name}
                    </p>
                    <p className="mt-1 text-[0.875rem] text-charcoal/65">{item.detail}</p>
                  </div>
                  <div className="flex items-center gap-5">
                    <label className="sr-only" htmlFor={`qty-${item.id}`}>
                      Quantity for {item.name}
                    </label>
                    <select
                      id={`qty-${item.id}`}
                      value={item.quantity}
                      onChange={(event) => setQuantity(item.id, Number(event.target.value))}
                      className="h-10 rounded-full border border-charcoal/15 bg-transparent px-4 text-[0.875rem]"
                    >
                      {[0, 1, 2, 3, 4, 5].map((value) => (
                        <option key={value} value={value}>
                          {value === 0 ? "Remove" : value}
                        </option>
                      ))}
                    </select>
                    <span className="w-20 text-right text-[0.9375rem] font-medium">
                      {formatPrice(item.priceCents * item.quantity)}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          {/* 2 — Delivery */}
          <section aria-labelledby="delivery-heading" className="mt-16">
            <Eyebrow>Step 2</Eyebrow>
            <h2 id="delivery-heading" className="mt-4 text-title">
              Delivery
            </h2>
            <div className="mt-7 grid gap-4 sm:grid-cols-2">
              {deliveryFields.map((field) => (
                <div
                  key={field.id}
                  className={field.width === "half" ? "sm:col-span-1" : "sm:col-span-2"}
                >
                  <label
                    htmlFor={field.id}
                    className="block text-mono uppercase text-label"
                  >
                    {field.label}
                  </label>
                  <input
                    id={field.id}
                    name={field.id}
                    type={field.type ?? "text"}
                    inputMode={field.inputMode}
                    autoComplete={field.autoComplete}
                    required
                    className="mt-3 h-12 w-full rounded-xl border border-charcoal/15 bg-white px-4 text-[0.9375rem] transition-colors duration-200 placeholder:text-charcoal/30 focus:border-charcoal focus:outline-none"
                  />
                </div>
              ))}
              <div className="sm:col-span-2">
                <label htmlFor="country" className="block text-mono uppercase text-label">
                  Country
                </label>
                <select
                  id="country"
                  name="country"
                  value={country}
                  onChange={(event) => setCountry(event.target.value)}
                  className="mt-3 h-12 w-full rounded-xl border border-charcoal/15 bg-white px-4 text-[0.9375rem] focus:border-charcoal focus:outline-none"
                >
                  {COUNTRIES.map((option) => (
                    <option key={option.code} value={option.code}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </section>

          {/* 3 — Payment */}
          <section aria-labelledby="payment-heading" className="mt-16">
            <Eyebrow>Step 3</Eyebrow>
            <h2 id="payment-heading" className="mt-4 text-title">
              Payment
            </h2>
            <fieldset className="mt-7">
              <legend className="sr-only">Payment method</legend>
              <div className="space-y-3">
                {PAYMENT_METHODS.map((method) => (
                  <label
                    key={method.id}
                    className={cx(
                      "flex cursor-pointer items-center justify-between gap-4 rounded-xl border p-4 transition-colors duration-200",
                      payment === method.id
                        ? "border-charcoal bg-white"
                        : "border-charcoal/12 hover:border-charcoal/35",
                    )}
                  >
                    <span className="flex items-center gap-4">
                      <input
                        type="radio"
                        name="payment"
                        value={method.id}
                        checked={payment === method.id}
                        onChange={() => setPayment(method.id)}
                        className="size-4 accent-[#191919]"
                      />
                      <span>
                        <span className="block text-[0.9375rem] font-medium">
                          {method.label}
                        </span>
                        <span className="mt-0.5 block text-[0.8125rem] text-charcoal/65">
                          {method.detail}
                        </span>
                      </span>
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>

            {/* Opt-in only, never pre-ticked, with the recurring charge stated. */}
            <label className="mt-6 flex cursor-pointer gap-4 rounded-xl border border-charcoal/12 p-5">
              <input
                type="checkbox"
                checked={repeat}
                onChange={(event) => setRepeat(event.target.checked)}
                className="mt-1 size-4 shrink-0 accent-[#191919]"
              />
              <span>
                <span className="block text-[0.9375rem] font-medium">
                  Send this programme again in 90 days
                </span>
                <span className="mt-1.5 block text-[0.8125rem] leading-relaxed text-charcoal/65">
                  Optional, and off unless you choose it. If you tick this, the same
                  programme is charged at {formatPrice(totalCents)} and shipped once, 90 days
                  from today. We email you 14 days before. Stop it any time from that email
                  or by writing to us — no notice period, no fee.
                </span>
              </span>
            </label>
          </section>

          {/* 4 — Confirm */}
          <section aria-labelledby="confirm-heading" className="mt-16">
            <h2 id="confirm-heading" className="sr-only">
              Confirm and order
            </h2>
            <label className="flex cursor-pointer gap-4">
              <input
                type="checkbox"
                checked={confirmedAge}
                onChange={(event) => setConfirmedAge(event.target.checked)}
                required
                className="mt-1 size-4 shrink-0 accent-[#191919]"
              />
              <span className="text-[0.875rem] leading-relaxed text-charcoal/65">
                I am 18 or over, and I have read the{" "}
                <Link href="/patient-information" className="underline underline-offset-4">
                  patient information
                </Link>{" "}
                for this medicine.
              </span>
            </label>

            {error ? (
              <p role="alert" className="mt-5 text-[0.875rem] text-charcoal">
                {error}
              </p>
            ) : null}

            <Button
              type="submit"
              size="lg"
              className="mt-8 w-full"
              disabled={submitting}
              arrow
            >
              {submitting ? "Completing…" : "Complete my order"}
            </Button>

            <p className="mt-5 text-xs leading-relaxed text-charcoal/65">
              No payment provider is connected in this build, so no money is taken and no
              order is dispatched. {mandatoryNotice}
            </p>
          </section>
        </form>

        {/* Summary */}
        <aside className="order-1 lg:order-2 lg:sticky lg:top-28 lg:self-start">
          <div className="rounded-[20px] bg-white p-7 shadow-[var(--shadow-card)] sm:p-8">
            <h2 className="text-mono uppercase text-label">Order summary</h2>
            <dl className="mt-7 space-y-4 text-[0.9375rem]">
              {items.map((item) => (
                <div key={item.id} className="flex justify-between gap-6">
                  <dt className="text-charcoal/65">
                    {item.name}
                    {item.quantity > 1 ? ` × ${item.quantity}` : ""}
                  </dt>
                  <dd>{formatPrice(item.priceCents * item.quantity)}</dd>
                </div>
              ))}
              <div className="flex justify-between gap-6 border-t border-charcoal/10 pt-4">
                <dt className="text-charcoal/65">Delivery</dt>
                <dd>Free</dd>
              </div>
              <div className="flex items-baseline justify-between gap-6 border-t border-charcoal/10 pt-4">
                <dt className="font-medium">Total</dt>
                <dd className="text-[1.5rem] font-semibold tracking-[-0.03em]">
                  {formatPrice(totalCents)}
                </dd>
              </div>
            </dl>
            <p className="mt-5 text-xs leading-relaxed text-charcoal/65">
              Including VAT. {repeat ? "Repeats once in 90 days, as selected." : "One-off charge — nothing renews."}
            </p>
          </div>

          <p className="mt-6 px-1 text-xs leading-relaxed text-charcoal/65">
            Questions before you order?{" "}
            <Link href="/contact" className="underline underline-offset-4">
              Contact us
            </Link>
            .
          </p>
        </aside>
      </div>
    </Container>
  );
}
