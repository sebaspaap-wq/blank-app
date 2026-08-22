import type { Metadata, Viewport } from "next";
import { DM_Sans, Playfair_Display } from "next/font/google";
import "./globals.css";

import { SiteProvider } from "@/components/site/SiteProvider";
import Navigation from "@/components/site/Navigation";
import Overlays from "@/components/site/Overlays";
import Footer from "@/components/site/Footer";
import RevealProvider from "@/components/ui/RevealProvider";

const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-playfair",
  display: "swap",
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  weight: ["300", "400"],
  variable: "--font-dm",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://cava.example"),
  title: {
    default: "CAVÁ — Luxury, Lived In.",
    template: "%s · CAVÁ",
  },
  description:
    "CAVÁ creates refined bathrobes designed to make everyday rituals feel extraordinary. The art of slow living.",
  keywords: ["CAVÁ", "luxury bathrobe", "cotton terry robe", "quiet luxury", "slow living"],
  openGraph: {
    title: "CAVÁ — Luxury, Lived In.",
    description:
      "Refined bathrobes designed to make everyday rituals feel extraordinary.",
    type: "website",
    locale: "en_GB",
    siteName: "CAVÁ",
    images: [{ url: "/images/og.jpg", width: 1200, height: 630, alt: "CAVÁ" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "CAVÁ — Luxury, Lived In.",
    description: "The art of slow living.",
    images: ["/images/og.jpg"],
  },
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
  },
};

export const viewport: Viewport = {
  themeColor: "#080807",
  colorScheme: "light",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${playfair.variable} ${dmSans.variable}`}>
      <body>
        <SiteProvider>
          <RevealProvider />
          <Navigation />
          <Overlays />
          <main id="main">{children}</main>
          <Footer />
        </SiteProvider>
      </body>
    </html>
  );
}
