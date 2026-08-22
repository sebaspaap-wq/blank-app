"use client";

import { useState } from "react";

export default function NewsletterForm() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "done">("idle");

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (!email.trim()) return;
        setState("done");
        setEmail("");
      }}
      className="relative mt-8 max-w-[24rem]"
    >
      <div className="flex items-center gap-4 border-b border-[rgba(245,242,235,0.28)] pb-3 transition-colors duration-700 focus-within:border-[rgba(245,242,235,0.85)]">
        <input
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="YOUR EMAIL"
          aria-label="Your email address"
          className="nav-label w-full bg-transparent text-ivory outline-none placeholder:text-[rgba(245,242,235,0.4)]"
        />
        <button
          type="submit"
          aria-label="Subscribe"
          className="cursor-pointer text-ivory transition-transform duration-700 hover:translate-x-1"
          style={{ transitionTimingFunction: "var(--ease)" }}
        >
          →
        </button>
      </div>
      <p
        className="eyebrow absolute mt-4 text-sand"
        style={{
          opacity: state === "done" ? 1 : 0,
          transform: `translateY(${state === "done" ? 0 : "4px"})`,
          transition: "opacity 0.8s var(--ease), transform 0.8s var(--ease)",
        }}
        aria-live="polite"
      >
        WELCOME TO CAVÁ
      </p>
    </form>
  );
}
