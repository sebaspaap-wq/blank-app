"use client";

import type { ReactNode } from "react";
import { ButtonLink } from "./Button";
import { track, type AnalyticsEvent, type AnalyticsPayload } from "@/lib/analytics";

type Props = {
  href: string;
  event: AnalyticsEvent;
  payload?: AnalyticsPayload;
  children: ReactNode;
  variant?: "solid" | "outline" | "inverse" | "outlineInverse" | "quiet";
  size?: "md" | "lg";
  className?: string;
  arrow?: boolean;
};

/** A CTA that reports itself to the funnel before navigating. */
export function TrackedLink({ href, event, payload, children, ...rest }: Props) {
  return (
    <ButtonLink href={href} onClick={() => track(event, payload)} {...rest}>
      {children}
    </ButtonLink>
  );
}
