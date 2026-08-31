import type { Metadata } from "next";
import { CheckoutClient } from "@/components/checkout/CheckoutClient";

export const metadata: Metadata = {
  title: "Checkout",
  description: "Complete your QUITTER order.",
  robots: { index: false, follow: false },
};

export default function CheckoutPage() {
  return <CheckoutClient />;
}
