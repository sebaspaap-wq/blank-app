"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { track } from "@/lib/analytics";
import { allowAll, denyAll, readConsent, writeConsent } from "@/lib/consent";
import { cx } from "@/lib/format";

/**
 * Cookie consent.
 *
 * Nothing non-essential runs before a choice is made: analytics events are
 * queued by `lib/analytics` and only leave the browser once analytics is
 * allowed. Refusing is exactly as easy as accepting.
 */
export function CookieConsent() {
  const [visible, setVisible] = useState(false);
  const [detail, setDetail] = useState(false);

  useEffect(() => {
    if (!readConsent()) {
      // Let the page settle before asking, so it never competes with the hero.
      const timer = window.setTimeout(() => setVisible(true), 900);
      return () => window.clearTimeout(timer);
    }
  }, []);

  const decide = (accepted: boolean) => {
    writeConsent(accepted ? allowAll() : denyAll());
    setVisible(false);
    track("consent_decision", { label: accepted ? "accepted_all" : "essential_only" });
  };

  if (!visible) return null;

  return (
    <div
      role="dialog"
      aria-modal="false"
      aria-labelledby="consent-title"
      className={cx(
        "fixed bottom-0 left-0 right-0 z-[60] p-4 sm:left-auto sm:ml-auto sm:max-w-[26rem] sm:p-6",
        "pb-[max(1rem,env(safe-area-inset-bottom))]",
      )}
    >
      <div className="rounded-[18px] bg-charcoal p-6 text-bone shadow-[0_30px_60px_-30px_rgba(0,0,0,0.85)]">
        <h2 id="consent-title" className="text-mono uppercase text-taupe">
          Cookies
        </h2>
        <p className="mt-4 text-[0.875rem] leading-relaxed text-bone/65">
          Essential cookies keep the shop working. Analytics cookies are off unless you
          allow them, and nothing is used to profile you or infer anything about your
          health.
        </p>

        <button
          type="button"
          onClick={() => setDetail((open) => !open)}
          className="mt-3 text-[0.8125rem] text-bone/60 underline underline-offset-4 hover:text-bone"
        >
          {detail ? "Hide details" : "What is stored?"}
        </button>

        {detail ? (
          <dl className="mt-4 space-y-3 border-t border-bone/12 pt-4 text-[0.8125rem] text-bone/55">
            <div>
              <dt className="text-bone/80">Essential</dt>
              <dd>Your bag and this choice. Always on, never shared.</dd>
            </div>
            <div>
              <dt className="text-bone/80">Analytics</dt>
              <dd>Aggregated page and funnel events. Off until you allow them.</dd>
            </div>
          </dl>
        ) : null}

        <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:[&>*]:flex-1">
          <Button variant="outlineInverse" onClick={() => decide(false)}>
            Essential only
          </Button>
          <Button variant="inverse" onClick={() => decide(true)}>
            Allow analytics
          </Button>
        </div>

        <p className="mt-4 text-xs text-bone/55">
          Change it any time in our{" "}
          <Link href="/privacy" className="underline underline-offset-4 hover:text-bone">
            privacy statement
          </Link>
          .
        </p>
      </div>
    </div>
  );
}
