"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { PackShot } from "./PackShot";
import { track } from "@/lib/analytics";
import {
  daysFromProgress,
  getJourney,
  subscribeJourney,
  unlockZero,
  useJourney,
} from "@/lib/journey";

/**
 * The QUITTER ZERO vault.
 *
 * The pack is not shown. It is sealed behind a lock that opens when the visitor
 * reaches day 90 on the timeline — the same thing the programme asks of them,
 * asked of the page. Pressing the lock early nudges it and says how far there is
 * left to go; pressing it once day 90 is reached opens it, so the moment is
 * reachable by keyboard and not only by scrolling.
 */

type VaultState = "locked" | "unlocking" | "unlocked";

export function ZeroVault({
  unlockOn = "timeline",
  onStateChange,
}: {
  /** "timeline" waits for the 90-day timeline; "view" waits for the vault itself. */
  unlockOn?: "timeline" | "view";
  onStateChange?: (state: VaultState) => void;
}) {
  const { progress } = useJourney();
  const [state, setState] = useState<VaultState>("locked");
  const [nudging, setNudging] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);
  const stateRef = useRef<VaultState>("locked");
  const inViewRef = useRef(false);

  const days = daysFromProgress(progress);

  useEffect(() => {
    stateRef.current = state;
    onStateChange?.(state);
  }, [state, onStateChange]);

  /**
   * The seal opens only when both are true: the visitor is looking at it, and
   * the 90 days are behind them. A fast scroll past the timeline must never
   * spend the moment off-screen.
   */
  const openIfEarned = useCallback(() => {
    if (stateRef.current !== "locked" || !inViewRef.current) return;
    if (unlockOn === "timeline" && getJourney().progress < 0.995) return;

    setState("unlocking");
    unlockZero();
    track("zero_unlocked", { label: unlockOn });
    window.setTimeout(() => setState("unlocked"), 1800);
  }, [unlockOn]);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          observer.disconnect();
          inViewRef.current = true;
          // A beat of stillness first, so the reveal reads as an event and not
          // as something that already happened while scrolling.
          window.setTimeout(openIfEarned, 700);
        }
      },
      { threshold: 0.55 },
    );

    observer.observe(node);
    // Progress can also arrive after the vault is on screen — on a phone the
    // timeline is often still being scrolled while the vault is in view.
    const unsubscribe = subscribeJourney(openIfEarned);

    return () => {
      observer.disconnect();
      unsubscribe();
    };
  }, [openIfEarned]);

  const handleSealPress = () => {
    if (state !== "locked") return;
    setNudging(true);
    window.setTimeout(() => setNudging(false), 600);
    track("zero_lock_nudged", { label: `day_${days}` });
  };

  return (
    <div
      ref={ref}
      data-state={state}
      data-nudge={nudging ? "true" : "false"}
      className="relative mx-auto aspect-square w-full max-w-[24rem] sm:max-w-[30rem]"
    >
      {/* Light behind the seal, released when it opens */}
      <div
        aria-hidden="true"
        className="vault-bloom absolute inset-[6%] rounded-full"
        style={{
          background:
            "radial-gradient(circle at 50% 44%, rgba(233,224,209,0.55) 0%, rgba(166,155,141,0.32) 38%, rgba(166,155,141,0) 72%)",
        }}
      />

      <div className="vault-pack absolute inset-x-[10%] top-[8%] w-[80%]" aria-hidden={state === "locked"}>
        <PackShot
          strength="0 mg"
          descriptor="Quitter Zero"
          footnote="Not for sale"
          finish="charcoal"
          angle={-14}
        />
      </div>

      {/* The seal */}
      <div className="vault-seal absolute inset-0">
        <button
          type="button"
          onClick={handleSealPress}
          aria-expanded={state !== "locked"}
          className="group absolute inset-0 w-full cursor-pointer overflow-hidden rounded-[22px] text-left"
        >
          <span className="sr-only">
            {state === "locked"
              ? `QUITTER ZERO is sealed. ${90 - days} of the 90 days to go — keep scrolling the timeline to open it.`
              : "QUITTER ZERO is unlocked."}
          </span>

          {/* Two halves of the door */}
          <span
            aria-hidden="true"
            className="vault-half vault-half--left absolute inset-y-0 left-0 w-1/2 border border-r-0 border-bone/12 rounded-l-[22px]"
            style={{
              background:
                "linear-gradient(122deg,#242424 0%,#1b1b1b 55%,#141414 100%)",
              boxShadow: "inset -1px 0 0 rgba(247,246,242,0.06)",
            }}
          />
          <span
            aria-hidden="true"
            className="vault-half vault-half--right absolute inset-y-0 right-0 w-1/2 border border-l-0 border-bone/12 rounded-r-[22px]"
            style={{
              background:
                "linear-gradient(122deg,#1b1b1b 0%,#161616 45%,#101010 100%)",
              boxShadow: "inset 1px 0 0 rgba(247,246,242,0.06)",
            }}
          />

          <span aria-hidden="true" className="vault-face absolute inset-0">
            {/* The mark, split by the seam */}
            <span className="pointer-events-none absolute inset-0 flex items-center justify-center">
              <span
                className="text-[13rem] font-semibold leading-none tracking-[-0.06em] sm:text-[17rem]"
                style={{
                  color: "transparent",
                  WebkitTextStroke: "1px rgba(166,155,141,0.26)",
                }}
              >
                0
              </span>
            </span>

            {/* Lock */}
            <span className="vault-lock absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-5">
              <svg
                width="54"
                height="66"
                viewBox="0 0 54 66"
                fill="none"
                className="drop-shadow-[0_10px_24px_rgba(0,0,0,0.55)]"
              >
                <g className="vault-shackle">
                  <path
                    d="M15 27V18a12 12 0 0 1 24 0v9"
                    stroke="#a69b8d"
                    strokeWidth="3"
                    strokeLinecap="round"
                  />
                </g>
                <rect x="6" y="27" width="42" height="33" rx="7" fill="#f7f6f2" fillOpacity="0.94" />
                <circle cx="27" cy="41" r="4" fill="#191919" />
                <rect x="25.4" y="43" width="3.2" height="8" rx="1.6" fill="#191919" />
              </svg>

              <span className="text-mono uppercase text-taupe transition-colors duration-300 group-hover:text-bone">
                Sealed until day 90
              </span>
            </span>

            {/* Progress read-out on the door itself */}
            <span className="absolute inset-x-0 bottom-7 flex flex-col items-center gap-3">
              <span className="text-mono uppercase text-bone/55">
                {nudging
                  ? `Not yet — ${90 - days} days to go`
                  : `Day ${String(days).padStart(2, "0")} of 90`}
              </span>
              <span className="h-px w-[42%] overflow-hidden bg-bone/15">
                <span
                  className="block h-px origin-left bg-taupe transition-transform duration-300 ease-out"
                  style={{ transform: `scaleX(${Math.max(progress, 0.02)})` }}
                />
              </span>
            </span>
          </span>

        </button>
      </div>
    </div>
  );
}
