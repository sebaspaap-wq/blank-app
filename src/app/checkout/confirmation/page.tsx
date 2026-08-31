import type { Metadata } from "next";
import { ConfirmationClient } from "@/components/checkout/ConfirmationClient";

export const metadata: Metadata = {
  title: "Order confirmed",
  robots: { index: false, follow: false },
};

export default function ConfirmationPage() {
  return <ConfirmationClient />;
}
